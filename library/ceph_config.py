# Copyright Red Hat
# SPDX-License-Identifier: Apache-2.0
# Author: Guillaume Abrioux <gabrioux@redhat.com>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule  # type: ignore
try:
    from ansible.module_utils.ca_common import exit_module, generate_cmd, fatal, is_containerized  # type: ignore
except ImportError:
    from module_utils.ca_common import exit_module, generate_cmd, fatal, is_containerized  # type: ignore

import datetime
import json

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_config
short_description: set ceph config
version_added: "2.10"
description:
    - Set Ceph config options.
options:
    fsid:
        description:
            - the fsid of the Ceph cluster to interact with.
        required: false
    image:
        description:
            - The Ceph container image to use.
        required: false
    action:
        description:
            - whether to get or set the parameter specified in 'option'
        required: false
        default: 'set'
    who:
        description:
            - which daemon the configuration should be set to
        required: true
    option:
        description:
            - name of the parameter to be set
        required: true
    value:
        description:
            - value of the parameter
        required: true if action is 'set'

author:
    - Guillaume Abrioux <gabrioux@redhat.com>
'''

EXAMPLES = '''
- name: set osd_memory_target for osd.0
  ceph_config:
    action: set
    who: osd.0
    option: osd_memory_target
    value: 5368709120

- name: set osd_memory_target for host ceph-osd-02
  ceph_config:
    action: set
    who: osd/host:ceph-osd-02
    option: osd_memory_target
    value: 5368709120

- name: get osd_pool_default_size value
  ceph_config:
    action: get
    who: global
    option: osd_pool_default_size
    value: 1
'''

RETURN = '''#  '''


def set_option(module,
               who,
               option,
               value,
               container_image=None):

    args = []
    args.extend([who, option, value])

    cmd = generate_cmd(sub_cmd=['config', 'set'],
                       args=args,
                       cluster=module.params.get('cluster'),
                       container_image=container_image)

    rc, out, err = module.run_command(cmd)

    return rc, cmd, out.strip(), err


def rm_option(module,
              who,
              option,
              container_image=None):

    args = []
    args.extend([who, option])

    cmd = generate_cmd(sub_cmd=['config', 'rm'],
                       args=args,
                       cluster=module.params.get('cluster'),
                       container_image=container_image)

    rc, out, err = module.run_command(cmd)

    return rc, cmd, out.strip(), err


def get_config_dump(module, container_image=None):
    cmd = generate_cmd(sub_cmd=['config', 'dump', '--format', 'json'],
                       args=[],
                       cluster=module.params.get('cluster'),
                       container_image=container_image)
    rc, out, err = module.run_command(cmd)
    if rc:
        fatal(message=f"Can't get current configuration via `ceph config dump`.Error:\n{err}", module=module)
    out = out.strip()
    return rc, cmd, out, err


def get_current_value(who, option, config_dump):
    for config in config_dump:
        if config['section'] == who and config['name'] == option:
            return config['value']
    return None


def main() -> None:
    module = AnsibleModule(
        argument_spec=dict(
            who=dict(type='str', required=True),
            action=dict(type='str', required=False, choices=['get', 'set', 'rm'], default='set'),
            option=dict(type='str', required=True),
            value=dict(type='str', required=False),
            fsid=dict(type='str', required=False),
            image=dict(type='str', required=False),
            cluster=dict(type='str', required=False, default='ceph')
        ),
        supports_check_mode=True,
        required_if=[['action', 'set', ['value']]]
    )

    # Gather module parameters in variables
    who = module.params.get('who')
    option = module.params.get('option')
    value = module.params.get('value')
    action = module.params.get('action')

    container_image = is_containerized()

    if module.check_mode:
        module.exit_json(
            changed=False,
            stdout='',
            cmd=[],
            stderr='',
            rc=0,
            start='',
            end='',
            delta='',
        )

    startd = datetime.datetime.now()
    changed = False

    rc, cmd, out, err = get_config_dump(module, container_image=container_image)
    config_dump = json.loads(out)
    current_value = get_current_value(who, option, config_dump)

    if action == 'set':
        if current_value and value.lower() == current_value.lower():
            out = 'who={} option={} value={} already set. Skipping.'.format(who, option, value)
        else:
            rc, cmd, out, err = set_option(module, who, option, value, container_image=container_image)
            changed = True
    elif action == 'get':
        if current_value is None:
            out = ''
            err = 'No value found for who={} option={}'.format(who, option)
        else:
            out = current_value
    elif action == 'rm':
        if current_value:
            rc, cmd, out, err = rm_option(module, who, option, container_image=container_image)
            changed = True

    exit_module(module=module, out=out, rc=rc,
                cmd=cmd, err=err, startd=startd,
                changed=changed)


if __name__ == '__main__':
    main()
