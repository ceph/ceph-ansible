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
    from ansible.module_utils.ca_common import exit_module
except ImportError:
    from module_utils.ca_common import exit_module
import datetime


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cephadm_bootstrap
short_description: Bootstrap a Ceph cluster via cephadm
version_added: "2.8"
description:
    - Bootstrap a Ceph cluster via cephadm
options:
    mon_ip:
        description:
            - Ceph monitor IP address.
        required: true
    image:
        description:
            - Ceph container image.
        required: false
    docker:
        description:
            - Use docker instead of podman.
        required: false
    fsid:
        description:
            - Ceph FSID.
        required: false
    pull:
        description:
            - Pull the Ceph container image.
        required: false
        default: true
    dashboard:
        description:
            - Deploy the Ceph dashboard.
        required: false
        default: true
    dashboard_user:
        description:
            - Ceph dashboard user.
        required: false
    dashboard_password:
        description:
            - Ceph dashboard password.
        required: false
    monitoring:
        description:
            - Deploy the monitoring stack.
        required: false
        default: true
    firewalld:
        description:
            - Manage firewall rules with firewalld.
        required: false
        default: true
    allow_overwrite:
        description:
            - allow overwrite of existing –output-* config/keyring/ssh files.
        required: false
        default: false
    registry_url:
        description:
            - URL for custom registry.
        required: false
    registry_username:
        description:
            - Username for custom registry.
        required: false
    registry_password:
        description:
            - Password for custom registry.
        required: false
    registry_json:
        description:
            - JSON file with custom registry login info (URL,
              username, password).
        required: false
    ssh_user:
        description:
            - SSH user used for cephadm ssh to the hosts.
        required: false
    ssh_config:
        description:
            - SSH config file path for cephadm ssh client.
        required: false
author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: bootstrap a cluster via cephadm (with default values)
  cephadm_bootstrap:
    mon_ip: 192.168.42.1

- name: bootstrap a cluster via cephadm (with custom values)
  cephadm_bootstrap:
    mon_ip: 192.168.42.1
    fsid: 3c9ba63a-c7df-4476-a1e7-317dfc711f82
    image: quay.ceph.io/ceph/daemon-base:latest-main-devel
    dashboard: false
    monitoring: false
    firewalld: false

- name: bootstrap a cluster via cephadm with custom image via env var
  cephadm_bootstrap:
    mon_ip: 192.168.42.1
  environment:
    CEPHADM_IMAGE: quay.ceph.io/ceph/daemon-base:latest-main-devel
'''

RETURN = '''#  '''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            mon_ip=dict(type='str', required=True),
            image=dict(type='str', required=False),
            docker=dict(type='bool', required=False, default=False),
            fsid=dict(type='str', required=False),
            pull=dict(type='bool', required=False, default=True),
            dashboard=dict(type='bool', required=False, default=True),
            dashboard_user=dict(type='str', required=False),
            dashboard_password=dict(type='str', required=False, no_log=True),
            monitoring=dict(type='bool', required=False, default=True),
            firewalld=dict(type='bool', required=False, default=True),
            allow_overwrite=dict(type='bool', required=False, default=False),
            registry_url=dict(type='str', require=False),
            registry_username=dict(type='str', require=False),
            registry_password=dict(type='str', require=False, no_log=True),
            registry_json=dict(type='path', require=False),
            ssh_user=dict(type='str', required=False),
            ssh_config=dict(type='str', required=False),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ('registry_json', 'registry_url'),
            ('registry_json', 'registry_username'),
            ('registry_json', 'registry_password'),
        ],
        required_together=[
            ('registry_url', 'registry_username', 'registry_password')
        ],
    )

    mon_ip = module.params.get('mon_ip')
    docker = module.params.get('docker')
    image = module.params.get('image')
    fsid = module.params.get('fsid')
    pull = module.params.get('pull')
    dashboard = module.params.get('dashboard')
    dashboard_user = module.params.get('dashboard_user')
    dashboard_password = module.params.get('dashboard_password')
    monitoring = module.params.get('monitoring')
    firewalld = module.params.get('firewalld')
    allow_overwrite = module.params.get('allow_overwrite')
    registry_url = module.params.get('registry_url')
    registry_username = module.params.get('registry_username')
    registry_password = module.params.get('registry_password')
    registry_json = module.params.get('registry_json')
    ssh_user = module.params.get('ssh_user')
    ssh_config = module.params.get('ssh_config')

    startd = datetime.datetime.now()

    cmd = ['cephadm']

    if docker:
        cmd.append('--docker')

    if image:
        cmd.extend(['--image', image])

    cmd.extend(['bootstrap', '--mon-ip', mon_ip])

    if fsid:
        cmd.extend(['--fsid', fsid])

    if not pull:
        cmd.append('--skip-pull')

    if dashboard:
        if dashboard_user:
            cmd.extend(['--initial-dashboard-user', dashboard_user])
        if dashboard_password:
            cmd.extend(['--initial-dashboard-password', dashboard_password])
    else:
        cmd.append('--skip-dashboard')

    if not monitoring:
        cmd.append('--skip-monitoring-stack')

    if not firewalld:
        cmd.append('--skip-firewalld')

    if allow_overwrite:
        cmd.append('--allow-overwrite')

    if registry_url and registry_username and registry_password:
        cmd.extend(['--registry-url', registry_url,
                    '--registry-username', registry_username,
                    '--registry-password', registry_password])

    if registry_json:
        cmd.extend(['--registry-json', registry_json])

    if ssh_user:
        cmd.extend(['--ssh-user', ssh_user])

    if ssh_config:
        cmd.extend(['--ssh-config', ssh_config])

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
