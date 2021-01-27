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
    from ansible.module_utils.ca_common import exec_command, exit_module, fatal, generate_cmd, is_containerized
except ImportError:
    from module_utils.ca_common import exec_command, exit_module, fatal, generate_cmd, is_containerized
import datetime
import json


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: radosgw_zonegroup

short_description: Manage RADOS Gateway Zonegroup

version_added: "2.8"

description:
    - Manage RADOS Gateway zonegroup(s) creation, deletion and updates.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    name:
        description:
            - name of the RADOS Gateway zonegroup.
        required: true
    state:
        description:
            If 'present' is used, the module creates a zonegroup if it doesn't
            exist or update it if it already exists.
            If 'absent' is used, the module will simply delete the zonegroup.
            If 'info' is used, the module will return all details about the
            existing zonegroup (json formatted).
        required: false
        choices: ['present', 'absent', 'info']
        default: present
    realm:
        description:
            - name of the RADOS Gateway realm.
        required: true
    endpoints:
        description:
            - endpoints of the RADOS Gateway zonegroup.
        required: false
        default: []
    default:
        description:
            - set the default flag on the zonegroup.
        required: false
        default: false
    master:
        description:
            - set the master flag on the zonegroup.
        required: false
        default: false

author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: create a RADOS Gateway default zonegroup
  radosgw_zonegroup:
    name: foo
    realm: bar
    endpoints:
      - http://192.168.1.10:8080
      - http://192.168.1.11:8080
    default: true

- name: get a RADOS Gateway zonegroup information
  radosgw_zonegroup:
    name: foo
    realm: bar
    state: info

- name: delete a RADOS Gateway zonegroup
  radosgw_zonegroup:
    name: foo
    realm: bar
    state: absent
'''

RETURN = '''#  '''


def create_zonegroup(module, container_image=None):
    '''
    Create a new zonegroup
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm')
    endpoints = module.params.get('endpoints')
    default = module.params.get('default')
    master = module.params.get('master')

    args = ['create', '--rgw-realm=' + realm, '--rgw-zonegroup=' + name]

    if endpoints:
        args.extend(['--endpoints=' + ','.join(endpoints)])

    if default:
        args.append('--default')

    if master:
        args.append('--master')

    cmd = generate_cmd(sub_cmd=['zonegroup'], binary='radosgw-admin', cluster=cluster, args=args, container_image=container_image)

    return cmd


def modify_zonegroup(module, container_image=None):
    '''
    Modify a new zonegroup
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm')
    endpoints = module.params.get('endpoints')
    default = module.params.get('default')
    master = module.params.get('master')

    args = ['modify', '--rgw-realm=' + realm, '--rgw-zonegroup=' + name]

    if endpoints:
        args.extend(['--endpoints=' + ','.join(endpoints)])

    if default:
        args.append('--default')

    if master:
        args.append('--master')

    cmd = generate_cmd(sub_cmd=['zonegroup'], binary='radosgw-admin', cluster=cluster, args=args, container_image=container_image)

    return cmd


def get_zonegroup(module, container_image=None):
    '''
    Get existing zonegroup
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm')

    args = ['get', '--rgw-realm=' + realm, '--rgw-zonegroup=' + name, '--format=json']

    cmd = generate_cmd(sub_cmd=['zonegroup'], binary='radosgw-admin', cluster=cluster, args=args, container_image=container_image)

    return cmd


def get_realm(module, container_image=None):
    '''
    Get existing realm
    '''

    cluster = module.params.get('cluster')
    realm = module.params.get('realm')

    args = [
        'get',
        '--rgw-realm=' + realm,
        '--format=json'
    ]

    cmd = generate_cmd(sub_cmd=['realm'], binary='radosgw-admin', cluster=cluster, args=args, container_image=container_image)

    return cmd


def remove_zonegroup(module, container_image=None):
    '''
    Remove a zonegroup
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    realm = module.params.get('realm')

    args = ['delete', '--rgw-realm=' + realm, '--rgw-zonegroup=' + name]

    cmd = generate_cmd(sub_cmd=['zonegroup'], binary='radosgw-admin', cluster=cluster, args=args, container_image=container_image)

    return cmd


def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, choices=['present', 'absent', 'info'], default='present'),
        realm=dict(type='str', require=True),
        endpoints=dict(type='list', require=False, default=[]),
        default=dict(type='bool', required=False, default=False),
        master=dict(type='bool', required=False, default=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    # Gather module parameters in variables
    name = module.params.get('name')
    state = module.params.get('state')
    endpoints = module.params.get('endpoints')
    master = str(module.params.get('master')).lower()

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
        rc, cmd, out, err = exec_command(module, get_zonegroup(module, container_image=container_image))
        if rc == 0:
            zonegroup = json.loads(out)
            _rc, _cmd, _out, _err = exec_command(module, get_realm(module, container_image=container_image))
            if _rc != 0:
                fatal(_err, module)
            realm = json.loads(_out)
            current = {
                'endpoints': zonegroup['endpoints'],
                'master': zonegroup.get('is_master', 'false'),
                'realm_id': zonegroup['realm_id']
            }
            asked = {
                'endpoints': endpoints,
                'master': master,
                'realm_id': realm['id']
            }
            if current != asked:
                rc, cmd, out, err = exec_command(module, modify_zonegroup(module, container_image=container_image))
                changed = True
        else:
            rc, cmd, out, err = exec_command(module, create_zonegroup(module, container_image=container_image))
            changed = True

    elif state == "absent":
        rc, cmd, out, err = exec_command(module, get_zonegroup(module, container_image=container_image))
        if rc == 0:
            rc, cmd, out, err = exec_command(module, remove_zonegroup(module, container_image=container_image))
            changed = True
        else:
            rc = 0
            out = "Zonegroup {} doesn't exist".format(name)

    elif state == "info":
        rc, cmd, out, err = exec_command(module, get_zonegroup(module, container_image=container_image))

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)


def main():
    run_module()


if __name__ == '__main__':
    main()
