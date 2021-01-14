# Copyright 2021, Red Hat, Inc.
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
                                               exit_module
except ImportError:
    from module_utils.ca_common import generate_ceph_cmd, is_containerized, exec_command, exit_module

import datetime
import json


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_dashboard_iscsi

short_description: Manage Ceph Dashboard User

version_added: "2.8"

description:
    - Manage Ceph Dashboard iSCSI(s) gateway adding, deletion and list.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    url:
        description:
            - url of the Ceph Dashboard iSCSI gateway.
        required: false
    name:
        description:
            - name of the Ceph Dashboard iSCSI gateway.
        required: false
    state:
        description:
            If 'present' is used, the module adds a iSCSI gateway if it doesn't
            exist.
            If 'absent' is used, the module will simply delete the iSCSI gateway.
            If 'list' is used, the module will return the iSCSI gateway list (json formatted).
        required: false
        choices: ['present', 'absent', 'list']
        default: present
author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: add a Ceph Dashboard iSCSI gateway
  ceph_dashboard_iscsi:
    cluster: ceph
    url: https://foo:bar@192.168.42.1:5000/

- name: add a Ceph Dashboard iSCSI gateway with explicit name
  ceph_dashboard_iscsi:
    url: https://foo:bar@192.168.42.1:5000/
    name: gw00
    state: present

- name: delete a Ceph Dashboard iSCSI gateway
  ceph_dashboard_iscsi:
    name: gw00
    state: absent

- name: list the Ceph Dashboard iSCSI gateways
  ceph_dashboard_iscsi:
    state: list
'''

RETURN = '''#  '''


def add_iscsi_gateway(module, container_image=None):
    '''
    Add an iSCSI gateway
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['iscsi-gateway-add', '-i', '-']

    if name:
        args.append(name)

    cmd = generate_ceph_cmd(sub_cmd=['dashboard'], args=args, cluster=cluster, container_image=container_image, interactive=True)

    return cmd


def list_iscsi_gateway(module, container_image=None):
    '''
    List existing iSCSI gateways
    '''

    cluster = module.params.get('cluster')

    args = ['iscsi-gateway-list', '--format=json']

    cmd = generate_ceph_cmd(sub_cmd=['dashboard'], args=args, cluster=cluster, container_image=container_image)

    return cmd


def remove_iscsi_gateway(module, container_image=None):
    '''
    Remove an iSCSI gateway
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['iscsi-gateway-rm', name]

    cmd = generate_ceph_cmd(sub_cmd=['dashboard'], args=args, cluster=cluster, container_image=container_image)

    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=False, default='ceph'),
            url=dict(type='str', required=False, no_log=True),
            name=dict(type='str', required=False),
            state=dict(type='str', required=False, choices=['present', 'absent', 'list'], default='present'),
        ),
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['url']),
            ('state', 'absent', ['name'])
        ]
    )

    # Gather module parameters in variables
    url = module.params.get('url')
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

    rc, cmd, out, err = exec_command(module, list_iscsi_gateway(module, container_image=container_image))
    if state == "present":
        gws = json.loads(out)
        urls = list(map(lambda x: x["service_url"], gws["gateways"].values()))
        if url not in urls:
            rc, cmd, out, err = exec_command(module, add_iscsi_gateway(module, container_image=container_image), stdin=url)
            changed = True
    elif state == "absent":
        gws = json.loads(out)
        if name in gws["gateways"]:
            rc, cmd, out, err = exec_command(module, remove_iscsi_gateway(module, container_image=container_image))
            changed = True
        else:
            rc = 0
            out = "iSCSI gateway {} doesn't exist".format(name)

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)


if __name__ == '__main__':
    main()
