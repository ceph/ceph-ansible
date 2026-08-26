# Copyright 2026, Red Hat, Inc.
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
import os


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: radosgw_account

short_description: Manage RADOS Gateway Account

version_added: "6.0"

description:
    - Manage RADOS Gateway account(s) creation and deletion.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    account_id:
        description:
            - The account ID.
        required: true
    account_name:
        description:
            - The account name.
        required: false
        default: None
    email:
        description:
            - The account email.
        required: false
        default: None
    realm:
        description:
            - set the realm of the account.
        required: false
        default: None
    zonegroup:
        description:
            - set the zonegroup of the account.
        required: false
        default: None
    zone:
        description:
            - set the zone of the account.
        required: false
        default: None
    state:
        description:
            If 'present' is used, the module creates an account if it doesn't exist.
            If 'absent' is used, the module will simply delete the account.
        required: false
        choices: ['present', 'absent']
        default: present

author:
    - Steffen Bohr <steffen.bohr@github.execve.de>
'''

EXAMPLES = '''
- name: create a RADOS Gateway account
  radosgw_account:
    account_id: RGW00000000000000001
    account_name: my-account

- name: delete a RADOS Gateway account
  radosgw_account:
    account_id: RGW00000000000000001
    state: absent
'''

RETURN = '''#  '''


def container_exec(binary, container_image):
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
    if os.environ.get('CEPH_CONTAINER_IMAGE'):
        container_image = os.getenv('CEPH_CONTAINER_IMAGE')
    else:
        container_image = None
    return container_image


def pre_generate_radosgw_cmd(container_image=None):
    if container_image:
        cmd = container_exec('radosgw-admin', container_image)
    else:
        cmd = ['radosgw-admin']
    return cmd


def generate_radosgw_cmd(cluster, args, container_image=None):
    cmd = pre_generate_radosgw_cmd(container_image=container_image)
    base_cmd = ['--cluster', cluster, 'account']
    cmd.extend(base_cmd + args)
    return cmd


def exec_commands(module, cmd):
    rc, out, err = module.run_command(cmd)
    return rc, cmd, out, err


def get_account(module, container_image=None):
    cluster = module.params.get('cluster')
    account_id = module.params.get('account_id')
    realm = module.params.get('realm', None)
    zonegroup = module.params.get('zonegroup', None)
    zone = module.params.get('zone', None)

    args = ['get', '--account-id=' + account_id, '--format=json']

    if realm:
        args.extend(['--rgw-realm=' + realm])
    if zonegroup:
        args.extend(['--rgw-zonegroup=' + zonegroup])
    if zone:
        args.extend(['--rgw-zone=' + zone])

    return generate_radosgw_cmd(cluster=cluster, args=args, container_image=container_image)


def create_account(module, container_image=None):
    cluster = module.params.get('cluster')
    account_id = module.params.get('account_id')
    account_name = module.params.get('account_name', None)
    email = module.params.get('email', None)
    realm = module.params.get('realm', None)
    zonegroup = module.params.get('zonegroup', None)
    zone = module.params.get('zone', None)

    args = ['create', '--account-id=' + account_id]

    if account_name:
        args.extend(['--account-name=' + account_name])
    if email:
        args.extend(['--email=' + email])
    if realm:
        args.extend(['--rgw-realm=' + realm])
    if zonegroup:
        args.extend(['--rgw-zonegroup=' + zonegroup])
    if zone:
        args.extend(['--rgw-zone=' + zone])

    return generate_radosgw_cmd(cluster=cluster, args=args, container_image=container_image)


def remove_account(module, container_image=None):
    cluster = module.params.get('cluster')
    account_id = module.params.get('account_id')
    realm = module.params.get('realm', None)
    zonegroup = module.params.get('zonegroup', None)
    zone = module.params.get('zone', None)

    args = ['rm', '--account-id=' + account_id]

    if realm:
        args.extend(['--rgw-realm=' + realm])
    if zonegroup:
        args.extend(['--rgw-zonegroup=' + zonegroup])
    if zone:
        args.extend(['--rgw-zone=' + zone])

    return generate_radosgw_cmd(cluster=cluster, args=args, container_image=container_image)


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
        account_id=dict(type='str', required=True),
        account_name=dict(type='str', required=False),
        email=dict(type='str', required=False),
        realm=dict(type='str', required=False),
        zonegroup=dict(type='str', required=False),
        zone=dict(type='str', required=False),
        state=dict(type='str', required=False, choices=['present', 'absent'], default='present'),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    account_id = module.params.get('account_id')
    state = module.params.get('state')

    startd = datetime.datetime.now()
    changed = False

    container_image = is_containerized()

    rc, cmd, out, err = exec_commands(module, get_account(module, container_image=container_image))

    if state == 'present':
        if rc != 0:
            changed = True
            if not module.check_mode:
                rc, cmd, out, err = exec_commands(module, create_account(module, container_image=container_image))
            else:
                rc = 0

    elif state == 'absent':
        if rc == 0:
            changed = True
            if not module.check_mode:
                rc, cmd, out, err = exec_commands(module, remove_account(module, container_image=container_image))
        else:
            rc = 0
            out = "Account {} doesn't exist".format(account_id)

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)


def main():
    run_module()


if __name__ == '__main__':
    main()
