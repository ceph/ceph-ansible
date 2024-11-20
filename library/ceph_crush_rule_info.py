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
        generate_cmd, \
        is_containerized, \
        exec_command
except ImportError:
    from module_utils.ca_common import exit_module, \
        generate_cmd, \
        is_containerized, \
        exec_command
import datetime


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_crush_rule_info
short_description: Lists Ceph Crush Replicated/Erasure Rules
version_added: "2.8"
description:
    - Retrieces Ceph Crush rule(s).
options:
    name:
        description:
            - name of the Ceph Crush rule. If state is 'info' - empty string
              can be provided as a value to get all crush rules
        required: true
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
author:
    - Teoman ONAY <@asm0deuz>
'''

EXAMPLES = '''
- name: get a Ceph Crush rule information
  ceph_crush_rule_info:
    name: foo
'''

RETURN = '''#  '''


def get_rule(module, container_image=None):
    '''
    Get existing crush rule
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['dump', name, '--format=json']

    cmd = generate_cmd(sub_cmd=['osd', 'crush', 'rule'],
                       args=args,
                       cluster=cluster,
                       container_image=container_image)

    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=False),
            cluster=dict(type='str', required=False, default='ceph'),
        ),
        supports_check_mode=True,
    )

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

    rc, cmd, out, err = exec_command(module, get_rule(module, container_image=container_image))  # noqa: E501

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)  # noqa: E501


if __name__ == '__main__':
    main()
