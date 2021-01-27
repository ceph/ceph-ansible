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
    from ansible.module_utils.ca_common import exec_command, exit_module, generate_cmd, is_containerized
except ImportError:
    from module_utils.ca_common import exec_command, exit_module, generate_cmd, is_containerized
import datetime


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: radosgw_realm

short_description: Manage RADOS Gateway Realm

version_added: "2.8"

description:
    - Manage RADOS Gateway realm(s) creation, deletion and updates.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    name:
        description:
            - name of the RADOS Gateway realm.
        required: true
    state:
        description:
            If 'present' is used, the module creates a realm if it doesn't
            exist or update it if it already exists.
            If 'absent' is used, the module will simply delete the realm.
            If 'info' is used, the module will return all details about the
            existing realm (json formatted).
        required: false
        choices: ['present', 'absent', 'info']
        default: present
    default:
        description:
            - set the default flag on the realm.
        required: false
        default: false

author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: create a RADOS Gateway default realm
  radosgw_realm:
    name: foo
    default: true

- name: get a RADOS Gateway realm information
  radosgw_realm:
    name: foo
    state: info

- name: delete a RADOS Gateway realm
  radosgw_realm:
    name: foo
    state: absent
'''

RETURN = '''#  '''


def create_realm(module, container_image=None):
    '''
    Create a new realm
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    default = module.params.get('default', False)

    args = ['create', '--rgw-realm=' + name]

    if default:
        args.append('--default')

    cmd = generate_cmd(sub_cmd=['realm'], binary='radosgw-admin', cluster=cluster, args=args, container_image=container_image)

    return cmd


def get_realm(module, container_image=None):
    '''
    Get existing realm
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['get', '--rgw-realm=' + name, '--format=json']

    cmd = generate_cmd(sub_cmd=['realm'], binary='radosgw-admin', cluster=cluster, args=args, container_image=container_image)

    return cmd


def remove_realm(module, container_image=None):
    '''
    Remove a realm
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['delete', '--rgw-realm=' + name]

    cmd = generate_cmd(sub_cmd=['realm'], binary='radosgw-admin', cluster=cluster, args=args, container_image=container_image)

    return cmd


def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, choices=['present', 'absent', 'info'], default='present'),
        default=dict(type='bool', required=False, default=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    # Gather module parameters in variables
    name = module.params.get('name')
    state = module.params.get('state')

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
        rc, cmd, out, err = exec_command(module, get_realm(module, container_image=container_image))
        if rc != 0:
            rc, cmd, out, err = exec_command(module, create_realm(module, container_image=container_image))
            changed = True

    elif state == "absent":
        rc, cmd, out, err = exec_command(module, get_realm(module, container_image=container_image))
        if rc == 0:
            rc, cmd, out, err = exec_command(module, remove_realm(module, container_image=container_image))
            changed = True
        else:
            rc = 0
            out = "Realm {} doesn't exist".format(name)

    elif state == "info":
        rc, cmd, out, err = exec_command(module, get_realm(module, container_image=container_image))

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)


def main():
    run_module()


if __name__ == '__main__':
    main()
