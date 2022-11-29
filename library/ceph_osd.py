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
    from ansible.module_utils.ca_common import exit_module, generate_cmd, is_containerized  # noqa: E501
except ImportError:
    from module_utils.ca_common import exit_module, generate_cmd, is_containerized  # noqa: E501
import datetime


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_osd
short_description: Manage Ceph OSD state
version_added: "2.8"
description:
    - Manage Ceph OSD state
options:
    ids:
        description:
            - The ceph OSD id(s).
        required: true
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    state:
        description:
            - The ceph OSD state.
        required: true
        choices: ['destroy', 'down', 'in', 'out', 'purge', 'rm']
author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: destroy OSD 42
  ceph_osd:
    ids: 42
    state: destroy

- name: set multiple OSDs down
  ceph_osd:
    ids: [0, 1, 3]
    state: down

- name: set OSD 42 in
  ceph_osd:
    ids: 42
    state: in

- name: set OSD 42 out
  ceph_osd:
    ids: 42
    state: out

- name: purge OSD 42
  ceph_osd:
    ids: 42
    state: purge

- name: rm OSD 42
  ceph_osd:
    ids: 42
    state: rm
'''

RETURN = '''#  '''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ids=dict(type='list', required=True),
            cluster=dict(type='str', required=False, default='ceph'),
            state=dict(type='str', required=True, choices=['destroy', 'down', 'in', 'out', 'purge', 'rm']),  # noqa: E501
        ),
        supports_check_mode=True,
    )

    ids = module.params.get('ids')
    cluster = module.params.get('cluster')
    state = module.params.get('state')

    if state in ['destroy', 'purge'] and len(ids) > 1:
        module.fail_json(msg='destroy and purge only support one OSD at at time', rc=1)  # noqa: E501

    startd = datetime.datetime.now()

    container_image = is_containerized()

    cmd = generate_cmd(sub_cmd=['osd', state], args=ids, cluster=cluster, container_image=container_image)  # noqa: E501

    if state in ['destroy', 'purge']:
        cmd.append('--yes-i-really-mean-it')

    if module.check_mode:
        exit_module(
            module=module,
            out='',
            rc=0,
            cmd=cmd,
            err='',
            startd=startd,
            changed=False
        )
    else:
        rc, out, err = module.run_command(cmd)
        changed = True
        if state in ['down', 'in', 'out'] and 'marked' not in err:
            changed = False
        exit_module(
            module=module,
            out=out,
            rc=rc,
            cmd=cmd,
            err=err,
            startd=startd,
            changed=changed
        )


if __name__ == '__main__':
    main()
