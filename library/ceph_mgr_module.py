# Copyright 2020, Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.ca_common import exit_module, \
                                               pre_generate_cmd, \
                                               generate_cmd, \
                                               is_containerized
except ImportError:
    from module_utils.ca_common import exit_module, \
                                       pre_generate_cmd, \
                                       generate_cmd, \
                                       is_containerized
import datetime
import json
import os


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_mgr_module
short_description: Manage Ceph MGR module
version_added: "2.8"
description:
    - Manage Ceph MGR module
options:
    name:
        description:
            - name of the ceph MGR module.
        required: true
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    state:
        description:
            - If 'enable' is used, the module enables the MGR module.
            If 'absent' is used, the module disables the MGR module.
            If 'auto', is used, the module does:
            enable all modules present in 'name',
            disable everything not listed in 'name',
            don't touch to anything listed in 'mgr_initial_modules' parameter.
        required: false
        choices: ['auto, 'enable', 'disable']
        default: auto
author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: enable some modules
  ceph_mgr_module:
    name:
      - dashboard
      - stats
      - alerts

- name: enable dashboard mgr module
  ceph_mgr_module:
    name: dashboard
    state: enable

- name: disable multiple mgr modules
  ceph_mgr_module:
    name: '{{ item }}'
    state: disable
  loop:
    - 'dashboard'
    - 'prometheus'
'''

RETURN = '''#  '''


def get_run_dir(module,
                cluster,
                container_image):
    cmd = generate_cmd(sub_cmd=['config'],
                       args=['get', 'mon', 'run_dir'],
                       cluster=cluster,
                       container_image=container_image)
    rc, out, err = module.run_command(cmd)
    if not rc and out:
        out = out.strip()
        return out
    else:
        raise RuntimeError("Can't retrieve run_dir config parameter")


def get_mgr_initial_modules(module,
                            cluster,
                            container_image):
    node_name = os.uname()[1]
    run_dir = get_run_dir(module, cluster, container_image)
    # /var/run/ceph/ceph-mon.mon0.asok
    socket_path = f"{run_dir}/{cluster}-mon.{node_name}.asok"
    cmd = pre_generate_cmd('ceph', container_image)
    cmd.extend(['--admin-daemon', socket_path, 'config', 'get', 'mgr_initial_modules', '--format', 'json'])
    rc, out, err = module.run_command(cmd)
    if not rc and out:
        out = json.loads(out)
        out = [m for m in out['mgr_initial_modules'].split()]
        return out
    else:
        raise RuntimeError(f"Can't retrieve 'mgr_initial_modules' config parameter.\ncmd={cmd}\nrc={rc}:\nstderr:\n{err}\n")


def mgr_module_ls(module, cluster, container_image):
    cmd = generate_cmd(sub_cmd=['mgr', 'module'],
                       args=['ls'],
                       cluster=cluster,
                       container_image=container_image)
    cmd.extend(['--format', 'json'])
    rc, out, err = module.run_command(cmd)
    if not rc and out:
        out = out.strip()
        out = json.loads(out)
        return out
    raise RuntimeError("Can't retrieve mgr module list")


def get_modules_from_reports(report):
    return ','.join([report[0] for report in report])


def get_cmd_from_reports(report):
    return [_report[4] for _report in report]


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='list', required=True),
            cluster=dict(type='str', required=False, default='ceph'),
            state=dict(type='str', required=False, default='auto', choices=['enable', 'auto', 'disable']),  # noqa: E501
        ),
        supports_check_mode=True,
    )

    name = module.params.get('name')
    cluster = module.params.get('cluster')
    state = module.params.get('state')

    startd = datetime.datetime.now()
    changed = False

    container_image = is_containerized()

    if module.check_mode:
        cmd = generate_cmd(sub_cmd=['mgr', 'module'],
                           args=['enable', 'noup'],
                           cluster=cluster,
                           container_image=container_image)
        exit_module(
            module=module,
            out='',
            rc=0,
            cmd=cmd,
            err='',
            startd=startd,
            changed=False
        )

    module_list = mgr_module_ls(module,
                                cluster=cluster,
                                container_image=container_image)
    enabled_modules = module_list['enabled_modules']
    disabled_modules = [module['name'] for module in module_list['disabled_modules']]
    always_on_modules = module_list['always_on_modules']
    mgr_initial_modules = get_mgr_initial_modules(module, cluster=cluster, container_image=container_image)

    ok_report = []
    fail_report = []
    skip_report = []
    cmd = []
    out = []
    err = []
    rc = 0

    if state in ['enable', 'disable']:
        for m in name:
            if m in always_on_modules:
                skip_report.append((m, 0, "{m} is always on, skipping", '',))
                continue
            _list_to_check = disabled_modules if state == 'disable' else enabled_modules
            if m not in _list_to_check:
                _cmd = generate_cmd(sub_cmd=['mgr', 'module'],
                                    args=[state, m],
                                    cluster=cluster,
                                    container_image=container_image)
                rc, _out, _err = module.run_command(_cmd)
                _report = (m, rc, _out, _err, _cmd,)
                if not rc:
                    ok_report.append(_report)
                else:
                    fail_report.append(_report)
            else:
                skip_report.append((m, 0, "{m} already {state}e, skipping.", '', [],))
        if not fail_report and not skip_report:
            changed = True

        if ok_report:
            out.append("Successfully {}d module(s): {}".format(state, get_modules_from_reports(ok_report)))
        if fail_report:
            err.append("Failed to {} module(s): {}".format(state, get_modules_from_reports(fail_report)))
            cmd = get_cmd_from_reports(fail_report)
        if skip_report:
            out.append("Skipped module(s): {}".format(get_modules_from_reports(skip_report)))

    if state == 'auto':
        to_enable = list(set(name) - set(enabled_modules))
        to_disable = list(set(enabled_modules) - set(name))

        enable_report = []
        disable_report = []
        for m in to_enable:
            _cmd = generate_cmd(sub_cmd=['mgr', 'module'],
                                args=['enable', m],
                                cluster=cluster,
                                container_image=container_image)
            _rc, _out, _err = module.run_command(_cmd)
            enable_report.append((m, _rc, _out, _err, _cmd,))
        for m in to_disable:
            if m in mgr_initial_modules:
                skip_report.append(m)
            else:
                _cmd = generate_cmd(sub_cmd=['mgr', 'module'],
                                    args=['disable', m],
                                    cluster=cluster,
                                    container_image=container_image)
                _rc, _out, _err = module.run_command(_cmd)
                disable_report.append((m, _rc, _out, _err, _cmd,))
        if not to_enable and len(to_disable) == len(skip_report):
            out = ['Nothing to do.']
        else:
            for _report in [enable_report, disable_report]:
                action = 'enable' if _report == enable_report else 'disable'
                if _report:
                    if any([report[1] for report in _report]):
                        rc = 1
                    module_ok = ','.join(sorted([report[0] for report in _report if not report[1]]))
                    module_failed = ','.join(sorted([report[0] for report in _report if report[1]]))
                    if module_ok:
                        out.append(f"action = {action} success for the following modules: {module_ok}")
                    if rc:
                        err_msg = "\n".join(sorted([report[3] for report in _report if report[1]]))
                        err.append(f'failed to enable module(s): {module_failed}. Error message(s):\n{err_msg}')
                cmd.extend([report[4] for report in _report if report[4]])
            if out:
                changed = True
    exit_module(
        module=module,
        out="\n".join(out),
        rc=rc,
        cmd=cmd,
        err="\n".join(err),
        startd=startd,
        changed=changed
    )


if __name__ == '__main__':
    main()
