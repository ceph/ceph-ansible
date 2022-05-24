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
import json


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cephadm_adopt
short_description: Adopt a Ceph cluster with cephadm
version_added: "2.8"
description:
    - Adopt a Ceph cluster with cephadm
options:
    name:
        description:
            - The ceph daemon name.
        required: true
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    style:
        description:
            - Cep deployment style.
        required: false
        default: legacy
    image:
        description:
            - Ceph container image.
        required: false
    docker:
        description:
            - Use docker instead of podman.
        required: false
    pull:
        description:
            - Pull the Ceph container image.
        required: false
        default: true
    firewalld:
        description:
            - Manage firewall rules with firewalld.
        required: false
        default: true
author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: adopt a ceph monitor with cephadm (default values)
  cephadm_adopt:
    name: mon.foo
    style: legacy

- name: adopt a ceph monitor with cephadm (with custom values)
  cephadm_adopt:
    name: mon.foo
    style: legacy
    image: quay.ceph.io/ceph/daemon-base:latest-main-devel
    pull: false
    firewalld: false

- name: adopt a ceph monitor with cephadm with custom image via env var
  cephadm_adopt:
    name: mon.foo
    style: legacy
  environment:
    CEPHADM_IMAGE: quay.ceph.io/ceph/daemon-base:latest-main-devel
'''

RETURN = '''#  '''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            cluster=dict(type='str', required=False, default='ceph'),
            style=dict(type='str', required=False, default='legacy'),
            image=dict(type='str', required=False),
            docker=dict(type='bool', required=False, default=False),
            pull=dict(type='bool', required=False, default=True),
            firewalld=dict(type='bool', required=False, default=True),
        ),
        supports_check_mode=True,
    )

    name = module.params.get('name')
    cluster = module.params.get('cluster')
    style = module.params.get('style')
    docker = module.params.get('docker')
    image = module.params.get('image')
    pull = module.params.get('pull')
    firewalld = module.params.get('firewalld')

    startd = datetime.datetime.now()

    cmd = ['cephadm', 'ls', '--no-detail']

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

    if rc == 0:
        if name in [x["name"] for x in json.loads(out) if x["style"] == "cephadm:v1"]:  # noqa: E501
            exit_module(
                module=module,
                out='{} is already adopted'.format(name),
                rc=0,
                cmd=cmd,
                err='',
                startd=startd,
                changed=False
            )
    else:
        module.fail_json(msg=err, rc=rc)

    cmd = ['cephadm']

    if docker:
        cmd.append('--docker')

    if image:
        cmd.extend(['--image', image])

    cmd.extend(['adopt', '--cluster', cluster, '--name', name, '--style', style])  # noqa: E501

    if not pull:
        cmd.append('--skip-pull')

    if not firewalld:
        cmd.append('--skip-firewalld')

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
