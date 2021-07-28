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
    interactive:
        description:
            - use password from file or stdin
        required: false
        default: True
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


def fatal(message, module):
    '''
    Report a fatal error and exit
    '''
    if module:
        module.fail_json(msg=message, rc=1)
    else:
        raise(Exception(message))


def container_exec(binary, container_image, interactive=False):
    '''
    Build the docker CLI to run a command inside a container
    '''

    container_binary = os.getenv('CEPH_CONTAINER_BINARY')
    command_exec = [container_binary, 'run']

    if interactive:
        command_exec.extend(['--interactive'])

    command_exec.extend(['--rm',
                         '--net=host',
                         '-v', '/etc/ceph:/etc/ceph:z',
                         '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                         '-v', '/var/log/ceph/:/var/log/ceph/:z',
                         '--entrypoint=' + binary, container_image])
    return command_exec


def is_containerized():
    '''
    Check if we are running on a containerized cluster
    '''

    if 'CEPH_CONTAINER_IMAGE' in os.environ:
        container_image = os.getenv('CEPH_CONTAINER_IMAGE')
    else:
        container_image = None

    return container_image


def pre_generate_ceph_cmd(container_image=None, interactive=False):
    '''
    Generate ceph prefix comaand
    '''
    if container_image:
        cmd = container_exec('ceph', container_image, interactive=interactive)
    else:
        cmd = ['ceph']

    return cmd


def generate_ceph_cmd(cluster, args, container_image=None, interactive=False):
    '''
    Generate 'ceph' command line to execute
    '''

    cmd = pre_generate_ceph_cmd(container_image=container_image, interactive=interactive)

    base_cmd = [
        '--cluster',
        cluster,
        'dashboard'
    ]

    cmd.extend(base_cmd + args)

    return cmd


def exec_commands(module, cmd, stdin=None):
    '''
    Execute command(s)
    '''

    binary_data = False
    if stdin:
        binary_data = True
    rc, out, err = module.run_command(cmd, data=stdin, binary_data=binary_data)

    return rc, cmd, out, err


def create_user(module, container_image=None):
    '''
    Create a new user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    interactive = module.params.get('interactive')

    if interactive:
        args = ['ac-user-create', '-i', '-',  name]
    else:
        password = module.params.get('password')
        args = ['ac-user-create', name, password]

    cmd = generate_ceph_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image,
                            interactive=interactive)

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

    cmd = generate_ceph_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image)

    return cmd


def set_password(module, container_image=None):
    '''
    Set user password
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    interactive = module.params.get('interactive')

    if interactive:
        args = ['ac-user-set-password', '-i', '-', name]
    else:
        password = module.params.get('password')
        args = ['ac-user-set-password', name, password]

    cmd = generate_ceph_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image,
                            interactive=interactive)

    return cmd


def get_user(module, container_image=None):
    '''
    Get existing user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['ac-user-show', name, '--format=json']

    cmd = generate_ceph_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image)

    return cmd


def remove_user(module, container_image=None):
    '''
    Remove a user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['ac-user-delete', name]

    cmd = generate_ceph_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image)

    return cmd


def exit_module(module, out, rc, cmd, err, startd, changed=False):
    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        rc=rc,
        stdout=out.rstrip("\r\n"),
        stderr=err.rstrip("\r\n"),
        changed=changed,
    )
    module.exit_json(**result)


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
        interactive=dict(type='bool', required=False, default=True),
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
    interactive = module.params.get('interactive')

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
        rc, cmd, out, err = exec_commands(module, get_user(module, container_image=container_image))  # noqa: E501
        stdin = password
        if not interactive:
            stdin = None
        if rc == 0:
            user = json.loads(out)
            user['roles'].sort()
            roles.sort()
            if user['roles'] != roles:
                rc, cmd, out, err = exec_commands(module, set_roles(module, container_image=container_image))  # noqa: E501
                changed = True
            rc, cmd, out, err = exec_commands(module, set_password(module, container_image=container_image), stdin=stdin)  # noqa: E501
        else:
            rc, cmd, out, err = exec_commands(module, create_user(module, container_image=container_image), stdin=stdin)  # noqa: E501
            if rc != 0:
                fatal(err, module)
            rc, cmd, out, err = exec_commands(module, set_roles(module, container_image=container_image))  # noqa: E501
            changed = True

    elif state == "absent":
        rc, cmd, out, err = exec_commands(module, get_user(module, container_image=container_image))  # noqa: E501
        if rc == 0:
            rc, cmd, out, err = exec_commands(module, remove_user(module, container_image=container_image))  # noqa: E501
            changed = True
        else:
            rc = 0
            out = "Dashboard User {} doesn't exist".format(name)

    elif state == "info":
        rc, cmd, out, err = exec_commands(module, get_user(module, container_image=container_image))  # noqa: E501

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)  # noqa: E501


def main():
    run_module()


if __name__ == '__main__':
    main()
