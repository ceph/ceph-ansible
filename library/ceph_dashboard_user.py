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
    from ansible.module_utils.ca_common import generate_ceph_cmd, \
                                               is_containerized, \
                                               exec_command, \
                                               exit_module, \
                                               fatal
except ImportError:
    from module_utils.ca_common import generate_ceph_cmd, is_containerized, exec_command, exit_module, fatal  # noqa: E501

import datetime
import json


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_dashboard_user

short_description: Manage Ceph Dashboard User

version_added: "2.8"

description:
    - Manage Ceph Dashboard user(s) creation, deletion and updates.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    name:
        description:
            - name of the Ceph Dashboard user.
        required: true
    state:
        description:
            If 'present' is used, the module creates a user if it doesn't
            exist or update it if it already exists.
            If 'absent' is used, the module will simply delete the user.
            If 'info' is used, the module will return all details about the
            existing user (json formatted).
        required: false
        choices: ['present', 'absent', 'info']
        default: present
    password:
        description:
            - password of the Ceph Dashboard user.
        required: false
    roles:
        description:
            - roles of the Ceph Dashboard user.
        required: false
        default: []

author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: create a Ceph Dashboard user
  ceph_dashboard_user:
    name: foo
    password: bar

- name: create a read-only/block-manager Ceph Dashboard user
  ceph_dashboard_user:
    name: foo
    password: bar
    roles:
      - 'read-only'
      - 'block-manager'

- name: create a Ceph Dashboard admin user
  ceph_dashboard_user:
    name: foo
    password: bar
    roles: ['administrator']

- name: get a Ceph Dashboard user information
  ceph_dashboard_user:
    name: foo
    state: info

- name: delete a Ceph Dashboard user
  ceph_dashboard_user:
    name: foo
    state: absent
'''

RETURN = '''#  '''


def create_user(module, container_image=None):
    '''
    Create a new user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['ac-user-create', '-i', '-',  name]

    cmd = generate_ceph_cmd(sub_cmd=['dashboard'],
                            args=args,
                            cluster=cluster,
                            container_image=container_image,
                            interactive=True)

    return cmd


def set_roles(module, container_image=None):
    '''
    Set user roles
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    roles = module.params.get('roles')

    args = ['ac-user-set-roles', name]

    args.extend(roles)

    cmd = generate_ceph_cmd(sub_cmd=['dashboard'],
                            args=args,
                            cluster=cluster,
                            container_image=container_image)

    return cmd


def set_password(module, container_image=None):
    '''
    Set user password
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['ac-user-set-password', '-i', '-', name]

    cmd = generate_ceph_cmd(sub_cmd=['dashboard'],
                            args=args,
                            cluster=cluster,
                            container_image=container_image,
                            interactive=True)

    return cmd


def get_user(module, container_image=None):
    '''
    Get existing user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['ac-user-show', name, '--format=json']

    cmd = generate_ceph_cmd(sub_cmd=['dashboard'],
                            args=args,
                            cluster=cluster,
                            container_image=container_image)

    return cmd


def remove_user(module, container_image=None):
    '''
    Remove a user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['ac-user-delete', name]

    cmd = generate_ceph_cmd(sub_cmd=['dashboard'],
                            args=args,
                            cluster=cluster,
                            container_image=container_image)

    return cmd


def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, choices=['present', 'absent', 'info'], default='present'),  # noqa: E501
        password=dict(type='str', required=False, no_log=True),
        roles=dict(type='list',
                   required=False,
                   choices=['administrator', 'read-only', 'block-manager', 'rgw-manager', 'cluster-manager', 'pool-manager', 'cephfs-manager'],  # noqa: E501
                   default=[]),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[['state', 'present', ['password']]]
    )

    # Gather module parameters in variables
    name = module.params.get('name')
    state = module.params.get('state')
    roles = module.params.get('roles')
    password = module.params.get('password')

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
        rc, cmd, out, err = exec_command(module, get_user(module, container_image=container_image))  # noqa: E501
        if rc == 0:
            user = json.loads(out)
            user['roles'].sort()
            roles.sort()
            if user['roles'] != roles:
                rc, cmd, out, err = exec_command(module, set_roles(module, container_image=container_image))  # noqa: E501
                changed = True
            rc, cmd, out, err = exec_command(module, set_password(module, container_image=container_image), stdin=password)  # noqa: E501
        else:
            rc, cmd, out, err = exec_command(module, create_user(module, container_image=container_image), stdin=password)  # noqa: E501
            if rc != 0:
                fatal(err, module)
            rc, cmd, out, err = exec_command(module, set_roles(module, container_image=container_image))  # noqa: E501
            changed = True

    elif state == "absent":
        rc, cmd, out, err = exec_command(module, get_user(module, container_image=container_image))  # noqa: E501
        if rc == 0:
            rc, cmd, out, err = exec_command(module, remove_user(module, container_image=container_image))  # noqa: E501
            changed = True
        else:
            rc = 0
            out = "Dashboard User {} doesn't exist".format(name)

    elif state == "info":
        rc, cmd, out, err = exec_command(module, get_user(module, container_image=container_image))  # noqa: E501

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)  # noqa: E501


def main():
    run_module()


if __name__ == '__main__':
    main()
