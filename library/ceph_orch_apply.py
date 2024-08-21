# Copyright Red Hat
# SPDX-License-Identifier: Apache-2.0
# Author: Guillaume Abrioux <gabrioux@redhat.com>
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
from typing import List, Tuple, Dict
__metaclass__ = type

import datetime
import yaml

from ansible.module_utils.basic import AnsibleModule  # type: ignore
try:
    from ansible.module_utils.ca_common import exit_module, build_base_cmd_orch  # type: ignore
except ImportError:
    from module_utils.ca_common import exit_module, build_base_cmd_orch


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_orch_apply
short_description: apply service spec
version_added: "2.9"
description:
    - apply a service spec
options:
    fsid:
        description:
            - the fsid of the Ceph cluster to interact with.
        required: false
    image:
        description:
            - The Ceph container image to use.
        required: false
    spec:
        description:
            - The service spec to apply
        required: true
author:
    - Guillaume Abrioux <gabrioux@redhat.com>
'''

EXAMPLES = '''
- name: apply osd spec
  ceph_orch_apply:
    spec: |
      service_type: osd
      service_id: osd
      placement:
        label: osds
      spec:
        data_devices:
          all: true
'''


def parse_spec(spec: str) -> Dict:
    """ parse spec string to yaml """
    yaml_spec = yaml.safe_load(spec)
    return yaml_spec


def retrieve_current_spec(module: AnsibleModule, expected_spec: Dict) -> Dict:
    """ retrieve current config of the service """
    service: str = expected_spec["service_type"]
    cmd = build_base_cmd_orch(module)
    cmd.extend(['ls', service])
    if 'service_name' in expected_spec:
        cmd.extend([expected_spec["service_name"]])
    else:
        cmd.extend([expected_spec["service_type"] + "." + expected_spec["service_id"]])
    cmd.extend(['--format=yaml'])
    out = module.run_command(cmd)
    if isinstance(out, str):
        # if there is no existing service, cephadm returns the string 'No services reported'
        return {}
    else:
        return yaml.safe_load(out[1])


def apply_spec(module: "AnsibleModule",
               data: str) -> Tuple[int, List[str], str, str]:
    cmd = build_base_cmd_orch(module)
    cmd.extend(['apply', '-i', '-'])
    rc, out, err = module.run_command(cmd, data=data)

    if rc:
        raise RuntimeError(err)

    return rc, cmd, out, err


def change_required(current: Dict, expected: Dict) -> bool:
    """ checks if the current config differs from what is expected """
    if not current:
        return True

    for key, value in expected.items():
        if key in current:
            if current[key] != value:
                return True
            continue
        else:
            return True
    return False


def run_module() -> None:

    module_args = dict(
        spec=dict(type='str', required=True),
        fsid=dict(type='str', required=False),
        docker=dict(type=bool,
                    required=False,
                    default=False),
        image=dict(type='str', required=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    startd = datetime.datetime.now()
    spec = module.params.get('spec')

    if module.check_mode:
        exit_module(
            module=module,
            out='',
            rc=0,
            cmd=[],
            err='',
            startd=startd,
            changed=False
        )

    # Idempotency check
    expected = parse_spec(module.params.get('spec'))
    current_spec = retrieve_current_spec(module, expected)

    if change_required(current_spec, expected):
        rc, cmd, out, err = apply_spec(module, spec)
        changed = True
    else:
        rc = 0
        cmd = []
        out = ''
        err = ''
        changed = False

    exit_module(
        module=module,
        out=out,
        rc=rc,
        cmd=cmd,
        err=err,
        startd=startd,
        changed=changed
    )


def main() -> None:
    run_module()


if __name__ == '__main__':
    main()
