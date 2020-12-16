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
                                               generate_ceph_cmd, \
                                               is_containerized
except ImportError:
    from module_utils.ca_common import exit_module, \
                                       generate_ceph_cmd, \
                                       is_containerized
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
    level:
        description:
            - This is applicable only when 'name' is 'noout'.
              This flag can be applied at several levels:
              1/ at the whole cluster level
              2/ at the bucket level
              3/ at the osd.X level
        required: false
        choices: ['osd', 'bucket', 'cluster']
        default: 'cluster'
    osd:
        description:
            - pass the osd when 'level' is 'osd'
        required: false
    bucket:
        description:
            - pass the bucket name when 'level' is 'bucket'
        required: false
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

- name: set noup flag on osd.123
  ceph_osd_flag:
    name: noup
    level: osd
    osd: osd.123

- name: unset noup flag on bucket 'host-456'
  ceph_osd_flag:
    state: absent
    name: noup
    level: bucket
    bucket: host-456
'''

RETURN = '''#  '''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, choices=['noup', 'nodown', 'noout', 'nobackfill', 'norebalance', 'norecover', 'noscrub', 'nodeep-scrub']),  # noqa: E501
            level=dict(type='str', required=False, default='cluster', choices=['cluster', 'bucket', 'osd']),
            osd=dict(type='str', required=False),
            bucket=dict(type='str', required=False),
            cluster=dict(type='str', required=False, default='ceph'),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),  # noqa: E501
        ),
        supports_check_mode=True,
        required_if=[
            ['level', 'osd', ['osd']],
            ['level', 'bucket', ['bucket']]
            ]
    )

    name = module.params.get('name')
    level = module.params.get('level')
    osd = module.params.get('osd')
    bucket = module.params.get('bucket')
    cluster = module.params.get('cluster')
    state = module.params.get('state')

    startd = datetime.datetime.now()

    container_image = is_containerized()

    osd_sub_cmd = ['osd']
    if name == 'noout' and level in ['osd', 'bucket']:
        if level == 'osd':
            action = ['add-noout'] if state == 'present' else ['rm-noout']
            name = osd
        if level == 'bucket':
            action = ['set-group', 'noout'] if state == 'present' else ['unset-group', 'noout']
            name = bucket
        osd_sub_cmd.extend(action)

    else:
        osd_sub_cmd.extend(['set']) if state == 'present' else osd_sub_cmd.extend(['unset'])

    cmd = generate_ceph_cmd(osd_sub_cmd, [name], cluster=cluster, container_image=container_image)

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
