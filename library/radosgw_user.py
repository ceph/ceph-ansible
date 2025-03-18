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
module: radosgw_user

short_description: Manage RADOS Gateway User

version_added: "2.8"

description:
    - Manage RADOS Gateway user(s) creation, deletion and updates.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    name:
        description:
            - name of the RADOS Gateway user (uid).
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
    display_name:
        description:
            - set the display name of the user.
        required: false
        default: None
    email:
        description:
            - set the email of the user.
        required: false
        default: None
    access_key:
        description:
            - set the S3 access key of the user.
        required: false
        default: None
    secret_key:
        description:
            - set the S3 secret key of the user.
        required: false
        default: None
    realm:
        description:
            - set the realm of the user.
        required: false
        default: None
    zonegroup:
        description:
            - set the zonegroup of the user.
        required: false
        default: None
    zone:
        description:
            - set the zone of the user.
        required: false
        default: None
    system:
        description:
            - set the system flag on the user.
        required: false
        default: false
    admin:
        description:
            - set the admin flag on the user.
        required: false
        default: false

author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: create a RADOS Gateway sytem user
  radosgw_user:
    name: foo
    system: true

- name: modify a RADOS Gateway user
  radosgw_user:
    name: foo
    email: foo@bar.io
    access_key: LbwDPp2BBo2Sdlts89Um
    secret_key: FavL6ueQWcWuWn0YXyQ3TnJ3mT3Uj5SGVHCUXC5K
    state: present

- name: get a RADOS Gateway user information
  radosgw_user:
    name: foo
    state: info

- name: delete a RADOS Gateway user
  radosgw_user:
    name: foo
    state: absent
'''

RETURN = '''#  '''


def container_exec(binary, container_image):
    '''
    Build the docker CLI to run a command inside a container
    '''

    container_binary = os.getenv('CEPH_CONTAINER_BINARY')
    command_exec = [container_binary,
                    'run',
                    '--rm',
                    '--net=host',
                    '-v', '/etc/ceph:/etc/ceph:z',
                    '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                    '-v', '/var/log/ceph/:/var/log/ceph/:z',
                    '--entrypoint=' + binary, container_image]
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


def pre_generate_radosgw_cmd(container_image=None):
    '''
    Generate radosgw-admin prefix comaand
    '''
    if container_image:
        cmd = container_exec('radosgw-admin', container_image)
    else:
        cmd = ['radosgw-admin']

    return cmd


def generate_radosgw_cmd(cluster, args, container_image=None):
    '''
    Generate 'radosgw' command line to execute
    '''

    cmd = pre_generate_radosgw_cmd(container_image=container_image)

    base_cmd = [
        '--cluster',
        cluster,
        'user'
    ]

    cmd.extend(base_cmd + args)

    return cmd


def generate_caps_cmd(cluster, args, container_image=None):
    '''
    Generate 'radosgw' command line to execute for caps
    '''

    cmd = pre_generate_radosgw_cmd(container_image=container_image)

    base_cmd = [
        '--cluster',
        cluster,
        'caps'
    ]

    cmd.extend(base_cmd + args)

    return cmd


def exec_commands(module, cmd):
    '''
    Execute command(s)
    '''

    rc, out, err = module.run_command(cmd)

    return rc, cmd, out, err


def create_user(module, container_image=None):
    '''
    Create a new user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    display_name = module.params.get('display_name')
    if not display_name:
        display_name = name
    email = module.params.get('email', None)
    access_key = module.params.get('access_key', None)
    secret_key = module.params.get('secret_key', None)
    realm = module.params.get('realm', None)
    zonegroup = module.params.get('zonegroup', None)
    zone = module.params.get('zone', None)
    system = module.params.get('system', False)
    admin = module.params.get('admin', False)
    caps = module.params.get('caps')

    args = ['create', '--uid=' + name, '--display_name=' + display_name]

    if email:
        args.extend(['--email=' + email])

    if access_key:
        args.extend(['--access-key=' + access_key])

    if secret_key:
        args.extend(['--secret-key=' + secret_key])

    if realm:
        args.extend(['--rgw-realm=' + realm])

    if zonegroup:
        args.extend(['--rgw-zonegroup=' + zonegroup])

    if zone:
        args.extend(['--rgw-zone=' + zone])

    if system:
        args.append('--system')

    if admin:
        args.append('--admin')

    if caps:
        caps_args = [f"{cap['type']}={cap['perm']}" for cap in caps]
        args.extend(['--caps=' + ';'.join(caps_args)])

    cmd = generate_radosgw_cmd(cluster=cluster,
                               args=args,
                               container_image=container_image)

    return cmd


def caps_add(module, caps, container_image=None):
    '''
    Create a new user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm', None)
    zonegroup = module.params.get('zonegroup', None)
    zone = module.params.get('zone', None)

    args = ['add', '--uid=' + name]

    if realm:
        args.extend(['--rgw-realm=' + realm])

    if zonegroup:
        args.extend(['--rgw-zonegroup=' + zonegroup])

    if zone:
        args.extend(['--rgw-zone=' + zone])

    caps_args = [f"{cap['type']}={cap['perm']}" for cap in caps]
    args.extend(['--caps=' + ';'.join(caps_args)])

    cmd = generate_caps_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image)

    return cmd


def caps_rm(module, caps, container_image=None):
    '''
    Create a new user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm', None)
    zonegroup = module.params.get('zonegroup', None)
    zone = module.params.get('zone', None)

    args = ['rm', '--uid=' + name]

    if realm:
        args.extend(['--rgw-realm=' + realm])

    if zonegroup:
        args.extend(['--rgw-zonegroup=' + zonegroup])

    if zone:
        args.extend(['--rgw-zone=' + zone])

    caps_args = [f"{cap['type']}={cap['perm']}" for cap in caps]
    args.extend(['--caps=' + ';'.join(caps_args)])

    cmd = generate_caps_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image)

    return cmd


def modify_user(module, container_image=None):
    '''
    Modify an existing user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    display_name = module.params.get('display_name')
    email = module.params.get('email', None)
    access_key = module.params.get('access_key', None)
    secret_key = module.params.get('secret_key', None)
    realm = module.params.get('realm', None)
    zonegroup = module.params.get('zonegroup', None)
    zone = module.params.get('zone', None)
    system = module.params.get('system', False)
    admin = module.params.get('admin', False)

    args = ['modify', '--uid=' + name]

    if display_name:
        args.extend(['--display_name=' + display_name])

    if email:
        args.extend(['--email=' + email])

    if access_key:
        args.extend(['--access-key=' + access_key])

    if secret_key:
        args.extend(['--secret-key=' + secret_key])

    if realm:
        args.extend(['--rgw-realm=' + realm])

    if zonegroup:
        args.extend(['--rgw-zonegroup=' + zonegroup])

    if zone:
        args.extend(['--rgw-zone=' + zone])

    if system:
        args.append('--system')

    if admin:
        args.append('--admin')

    cmd = generate_radosgw_cmd(cluster=cluster,
                               args=args,
                               container_image=container_image)

    return cmd


def get_user(module, container_image=None):
    '''
    Get existing user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm', None)
    zonegroup = module.params.get('zonegroup', None)
    zone = module.params.get('zone', None)

    args = ['info', '--uid=' + name, '--format=json']

    if realm:
        args.extend(['--rgw-realm=' + realm])

    if zonegroup:
        args.extend(['--rgw-zonegroup=' + zonegroup])

    if zone:
        args.extend(['--rgw-zone=' + zone])

    cmd = generate_radosgw_cmd(cluster=cluster,
                               args=args,
                               container_image=container_image)

    return cmd


def remove_user(module, container_image=None):
    '''
    Remove a user
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm', None)
    zonegroup = module.params.get('zonegroup', None)
    zone = module.params.get('zone', None)

    args = ['rm', '--uid=' + name]

    if realm:
        args.extend(['--rgw-realm=' + realm])

    if zonegroup:
        args.extend(['--rgw-zonegroup=' + zonegroup])

    if zone:
        args.extend(['--rgw-zone=' + zone])

    cmd = generate_radosgw_cmd(cluster=cluster,
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
        display_name=dict(type='str', required=False),
        email=dict(type='str', required=False),
        access_key=dict(type='str', required=False, no_log=True),
        secret_key=dict(type='str', required=False, no_log=True),
        realm=dict(type='str', required=False),
        zonegroup=dict(type='str', required=False),
        zone=dict(type='str', required=False),
        system=dict(type='bool', required=False, default=False),
        admin=dict(type='bool', required=False, default=False),
        caps=dict(type='list', required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    # Gather module parameters in variables
    name = module.params.get('name')
    state = module.params.get('state')
    display_name = module.params.get('display_name')
    if not display_name:
        display_name = name
    email = module.params.get('email')
    access_key = module.params.get('access_key')
    secret_key = module.params.get('secret_key')
    system = module.params.get('system')
    admin = module.params.get('admin')
    caps = module.params.get('caps')

    startd = datetime.datetime.now()
    changed = False

    # will return either the image name or None
    container_image = is_containerized()

    rc, cmd, out, err = exec_commands(module, get_user(module, container_image=container_image))  # noqa: E501
    if state == "present":
        if rc == 0:
            user = json.loads(out)
            current = {
                'display_name': user['display_name'],
                'system': user.get('system', False),
                'admin': user.get('admin', False),
            }
            asked = {
                'display_name': display_name,
                'system': system,
                'admin': admin,
            }
            if email:
                current['email'] = user['email']
                asked['email'] = email
            if caps:
                current['caps'] = user['caps']
                asked['caps'] = caps

            if access_key and secret_key:
                asked['access_key'] = access_key
                asked['secret_key'] = secret_key
                for key in user['keys']:
                    if key['access_key'] == access_key and key['secret_key'] == secret_key:  # noqa: E501
                        del asked['access_key']
                        del asked['secret_key']
                        break

            changed = current != asked
            if changed and not module.check_mode:
                rc, cmd, out, err = exec_commands(module, modify_user(module, container_image=container_image))

                if caps:
                    missing_caps = [cap for cap in asked['caps'] if cap not in current['caps']]
                    extra_caps = [cap for cap in current['caps'] if cap not in asked['caps']]
                    if extra_caps:
                        rc, cmd, out, err = exec_commands(module, caps_rm(module, extra_caps, container_image=container_image))
                    if missing_caps:
                        rc, cmd, out, err = exec_commands(module, caps_add(module, missing_caps, container_image=container_image))
        else:
            changed = True
            if not module.check_mode:
                rc, cmd, out, err = exec_commands(module, create_user(module, container_image=container_image))  # noqa: E501
            else:
                rc = 0

    elif state == "absent":
        if rc == 0:
            if not module.check_mode:
                rc, cmd, out, err = exec_commands(module, remove_user(module, container_image=container_image))  # noqa: E501
            changed = True
        else:
            rc = 0
            out = "User {} doesn't exist".format(name)

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)  # noqa: E501


def main():
    run_module()


if __name__ == '__main__':
    main()
