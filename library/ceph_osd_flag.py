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
    from ansible.module_utils.ca_common import exit_module, generate_ceph_cmd, is_containerized
except ImportError:
    from module_utils.ca_common import exit_module, generate_ceph_cmd, is_containerized
import datetime


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_osd_flag
short_description: Manage Ceph OSD flag
version_added: "2.8"
description:
    - Manage Ceph OSD flag
options:
    name:
        description:
            - name of the ceph OSD flag.
        required: true
        choices: ['noup', 'nodown', 'noout', 'nobackfill', 'norebalance', 'norecover', 'noscrub', 'nodeep-scrub']
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    state:
        description:
            - If 'present' is used, the module sets the OSD flag.
            If 'absent' is used, the module will unset the OSD flag.
        required: false
        choices: ['present', 'absent']
        default: present
author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: set noup OSD flag
  ceph_osd_flag:
    name: noup

- name: unset multiple OSD flags
  ceph_osd_flag:
    name: '{{ item }}'
    state: absent
  loop:
    - 'noup'
    - 'norebalance'
'''

RETURN = '''#  '''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, choices=['noup', 'nodown', 'noout', 'nobackfill', 'norebalance', 'norecover', 'noscrub', 'nodeep-scrub']),
            cluster=dict(type='str', required=False, default='ceph'),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True,
    )

    name = module.params.get('name')
    cluster = module.params.get('cluster')
    state = module.params.get('state')

    startd = datetime.datetime.now()

    container_image = is_containerized()

    if state == 'present':
        cmd = generate_ceph_cmd(['osd', 'set'], [name], cluster=cluster, container_image=container_image)
    else:
        cmd = generate_ceph_cmd(['osd', 'unset'], [name], cluster=cluster, container_image=container_image)

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
        exit_module(
            module=module,
            out=out,
            rc=rc,
            cmd=cmd,
            err=err,
            startd=startd,
            changed=True
        )


if __name__ == '__main__':
    main()
