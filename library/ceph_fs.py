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
    from ansible.module_utils.ca_common import is_containerized, \
                                               exec_command, \
                                               generate_cmd, \
                                               exit_module
except ImportError:
    from module_utils.ca_common import is_containerized, \
                                       exec_command, \
                                       generate_cmd, \
                                       exit_module

import datetime
import json


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_fs

short_description: Manage Ceph File System

version_added: "2.8"

description:
    - Manage Ceph File System(s) creation, deletion and updates.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    name:
        description:
            - name of the Ceph File System.
        required: true
    state:
        description:
            If 'present' is used, the module creates a filesystem if it
            doesn't  exist or update it if it already exists.
            If 'absent' is used, the module will simply delete the filesystem.
            If 'info' is used, the module will return all details about the
            existing filesystem (json formatted).
        required: false
        choices: ['present', 'absent', 'info']
        default: present
    data:
        description:
            - name of the data pool.
        required: false
    metadata:
        description:
            - name of the metadata pool.
        required: false
    max_mds:
        description:
            - name of the max_mds attribute.
        required: false
    max_file_size:
        description:
            - Maximum allowed file size for the filesystem.
        required: false
    allow_standby_replay:
        description:
            - Whether this CephFS allows standby-replay daemons.
        required: false
    info_param:
        description:
            - When C(state=info), return only a single parsed field in C(value).
        required: false
        choices: ['allow_standby_replay', 'max_mds', 'max_file_size', 'mds_in_count', 'mds_in_ranks']


author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: create a Ceph File System
  ceph_fs:
    name: foo
    data: bar_data
    metadata: bar_metadata
    max_mds: 2

- name: get a Ceph File System information
  ceph_fs:
    name: foo
    state: info

- name: delete a Ceph File System
  ceph_fs:
    name: foo
    state: absent
'''

RETURN = '''#  '''


def create_fs(module, container_image=None):
    '''
    Create a new fs
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    data = module.params.get('data')
    metadata = module.params.get('metadata')

    args = ['new', name, metadata, data]

    cmd = generate_cmd(sub_cmd=['fs'],
                       args=args,
                       cluster=cluster,
                       container_image=container_image)

    return cmd


def get_fs(module, container_image=None):
    '''
    Get existing fs
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['get', name, '--format=json']

    cmd = generate_cmd(sub_cmd=['fs'],
                       args=args,
                       cluster=cluster,
                       container_image=container_image)

    return cmd


def remove_fs(module, container_image=None):
    '''
    Remove a fs
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['rm', name, '--yes-i-really-mean-it']

    cmd = generate_cmd(sub_cmd=['fs'],
                       args=args,
                       cluster=cluster,
                       container_image=container_image)

    return cmd


def fail_fs(module, container_image=None):
    '''
    Fail a fs
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['fail', name]

    cmd = generate_cmd(sub_cmd=['fs'],
                       args=args,
                       cluster=cluster,
                       container_image=container_image)

    return cmd


def set_fs(module, param, value, container_image=None):
    '''
    Set parameter to a fs
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    args = ['set', name, str(param), str(value)]

    cmd = generate_cmd(sub_cmd=['fs'],
                       args=args,
                       cluster=cluster,
                       container_image=container_image)

    return cmd


def get_allow_standby_replay(fs):
    '''
    Return allow_standby_replay from fs json payload
    '''

    mdsmap = fs.get('mdsmap', {})
    flags_state = mdsmap.get('flags_state', {})
    return bool(flags_state.get('allow_standby_replay', mdsmap.get('allow_standby_replay', False)))


def parse_fs_info(out):
    '''
    Parse fs info output and return useful fields for playbooks.
    '''

    fs = json.loads(out)
    mdsmap = fs.get('mdsmap', {})
    return {
        'allow_standby_replay_current': get_allow_standby_replay(fs),
        'max_mds_current': mdsmap.get('max_mds'),
        'max_file_size_current': mdsmap.get('max_file_size'),
        'mds_in_ranks_current': mdsmap.get('in', []),
        'mds_in_count_current': len(mdsmap.get('in', [])),
    }


def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, choices=['present', 'absent', 'info'], default='present'),  # noqa: E501
        data=dict(type='str', required=False),
        metadata=dict(type='str', required=False),
        max_mds=dict(type='int', required=False),
        max_file_size=dict(type='int', required=False),
        allow_standby_replay=dict(type='bool', required=False),
        info_param=dict(type='str', required=False, choices=['allow_standby_replay', 'max_mds', 'max_file_size', 'mds_in_count', 'mds_in_ranks']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[['state', 'present', ['data', 'metadata']]],
    )

    # Gather module parameters in variables
    name = module.params.get('name')
    state = module.params.get('state')
    max_mds = module.params.get('max_mds')
    max_file_size = module.params.get('max_file_size')
    allow_standby_replay = module.params.get('allow_standby_replay')
    info_param = module.params.get('info_param')

    if module.check_mode:
        module.exit_json(
            changed=False,
            stdout='',
            stderr='',
            rc=0,
            start='',
            end='',
            delta='',
        )

    startd = datetime.datetime.now()
    changed = False

    # will return either the image name or None
    container_image = is_containerized()

    if state == "present":
        rc, cmd, out, err = exec_command(module, get_fs(module, container_image=container_image))  # noqa: E501
        if rc == 0:
            fs = json.loads(out)
            if max_mds and fs["mdsmap"]["max_mds"] != max_mds:
                rc, cmd, out, err = exec_command(module, set_fs(module, 'max_mds', max_mds, container_image=container_image))  # noqa: E501
                if rc == 0:
                    changed = True
            if max_file_size is not None and fs["mdsmap"]["max_file_size"] != max_file_size:
                rc, cmd, out, err = exec_command(module, set_fs(module, 'max_file_size', max_file_size, container_image=container_image))  # noqa: E501
                if rc == 0:
                    changed = True
            if allow_standby_replay is not None and get_allow_standby_replay(fs) != allow_standby_replay:
                rc, cmd, out, err = exec_command(module, set_fs(module, 'allow_standby_replay', 'true' if allow_standby_replay else 'false', container_image=container_image))  # noqa: E501
                if rc == 0:
                    changed = True
        else:
            rc, cmd, out, err = exec_command(module, create_fs(module, container_image=container_image))  # noqa: E501
            if max_mds and max_mds > 1:
                exec_command(module, set_fs(module, 'max_mds', max_mds, container_image=container_image))  # noqa: E501
            if max_file_size is not None:
                exec_command(module, set_fs(module, 'max_file_size', max_file_size, container_image=container_image))  # noqa: E501
            if allow_standby_replay:
                exec_command(module, set_fs(module, 'allow_standby_replay', 'true', container_image=container_image))  # noqa: E501
            if rc == 0:
                changed = True

    elif state == "absent":
        rc, cmd, out, err = exec_command(module, get_fs(module, container_image=container_image))  # noqa: E501
        if rc == 0:
            exec_command(module, fail_fs(module, container_image=container_image))  # noqa: E501
            rc, cmd, out, err = exec_command(module, remove_fs(module, container_image=container_image))  # noqa: E501
            if rc == 0:
                changed = True
        else:
            rc = 0
            out = "Ceph File System {} doesn't exist".format(name)

    elif state == "info":
        rc, cmd, out, err = exec_command(module, get_fs(module, container_image=container_image))  # noqa: E501
        if rc == 0:
            endd = datetime.datetime.now()
            delta = endd - startd
            parsed = parse_fs_info(out)
            if info_param == 'allow_standby_replay':
                value = parsed['allow_standby_replay_current']
            elif info_param == 'max_mds':
                value = parsed['max_mds_current']
            elif info_param == 'max_file_size':
                value = parsed['max_file_size_current']
            elif info_param == 'mds_in_count':
                value = parsed['mds_in_count_current']
            elif info_param == 'mds_in_ranks':
                value = parsed['mds_in_ranks_current']
            else:
                value = None
            module.exit_json(
                cmd=cmd,
                start=str(startd),
                end=str(endd),
                delta=str(delta),
                rc=rc,
                stdout=out.rstrip("\r\n"),
                stderr=err.rstrip("\r\n"),
                changed=changed,
                allow_standby_replay_current=parsed['allow_standby_replay_current'],
                max_mds_current=parsed['max_mds_current'],
                max_file_size_current=parsed['max_file_size_current'],
                mds_in_count_current=parsed['mds_in_count_current'],
                mds_in_ranks_current=parsed['mds_in_ranks_current'],
                value=value,
            )

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)  # noqa: E501


def main():
    run_module()


if __name__ == '__main__':
    main()
