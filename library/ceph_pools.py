#!/usr/bin/python
# Copyright 2018, Red Hat, Inc.
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


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_pool

author: Guillaume Abrioux <gabrioux@redhat.com>

short_description: Manage Ceph pool(s)

version_added: "2.4"

description:
    - Manage Ceph pools creation, deletion.
    It can also list and get information about pools.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
'''

RETURN = '''#  '''

from ansible.module_utils.basic import AnsibleModule
import datetime
import os
import struct
import time
import base64


def fatal(message, module):
    '''
    Report a fatal error and exit
    '''

    if module:
        module.fail_json(msg=message, rc=1)
    else:
        raise(Exception(message))

def generate_ceph_cmd(cluster, args, containerized=None):
    '''
    Generate 'ceph' command line to execute
    '''

    cmd = []

    base_cmd = [
        'ceph',
        '--cluster',
        cluster,
        'auth',
    ]

    cmd.extend(base_cmd + args)

    if containerized:
        cmd = containerized.split() + cmd

    return cmd

def exec_commands(module, cmd_list):
    '''
    Execute command(s)
    '''

    for cmd in cmd_list:
        rc, out, err = module.run_command(cmd)
        if rc != 0:
            return rc, cmd, out, err

    return rc, cmd, out, err

def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        name=dict(type='str', required=False),
        state=dict(type='str', required=True),
        containerized=dict(type='str', required=False, default=None),
        caps=dict(type='dict', required=False, default=None),
        secret=dict(type='str', required=False, default=None),
        import_key=dict(type='bool', required=False, default=True),
        auid=dict(type='str', required=False, default=None),
        dest=dict(type='str', required=False, default='/etc/ceph/'),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Gather module parameters in variables
    state = module.params['state']
    name = module.params.get('name')
    cluster = module.params.get('cluster')
    containerized = module.params.get('containerized')
    caps = module.params.get('caps')
    secret = module.params.get('secret')
    import_key = module.params.get('import_key')
    auid = module.params.get('auid')
    dest = module.params.get('dest')

    result = dict(
        changed=False,
        stdout='',
        stderr='',
        rc='',
        start='',
        end='',
        delta='',
    )

    if module.check_mode:
        return result

    startd = datetime.datetime.now()

    # Test if the key exists, if it does we skip its creation
    # We only want to run this check when a key needs to be added
    # There is no guarantee that any cluster is running and we don't need one
    if import_key:
        rc, cmd, out, err = exec_commands(
            module, info_key(cluster, name, containerized))

    if state == "present":
        if not caps:
            fatal("Capabilities must be provided when state is 'present'", module)

        # We allow 'present' to override any existing key ONLY if a secret is provided, if not we skip the creation
        if import_key:
            if rc == 0 and not secret:
                result["stdout"] = "skipped, since {0} already exists, if you want to update a key use 'state: update'".format(
                    name)
                result['rc'] = rc
                module.exit_json(**result)

        rc, cmd, out, err = exec_commands(module, create_key(
            module, result, cluster, name, secret, caps, import_key, auid, dest, containerized))

    elif state == "update":
        if not caps:
            fatal("Capabilities must be provided when state is 'update'", module)

        if rc != 0:
            result["stdout"] = "skipped, since {0} does not exist".format(name)
            result['rc'] = 0
            module.exit_json(**result)

        rc, cmd, out, err = exec_commands(
            module, update_key(cluster, name, caps, containerized))

    elif state == "absent":
        rc, cmd, out, err = exec_commands(
            module, delete_key(cluster, name, containerized))

    elif state == "info":
        if rc != 0:
            result["stdout"] = "skipped, since {0} does not exist".format(name)
            result['rc'] = 0
            module.exit_json(**result)

        rc, cmd, out, err = exec_commands(
            module, info_key(cluster, name, containerized))

    elif state == "list":
        rc, cmd, out, err = exec_commands(
            module, list_keys(cluster, containerized))

    else:
        module.fail_json(
            msg='State must either be "present" or "absent" or "update" or "list" or "info".', changed=False, rc=1)

    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        rc=rc,
        stdout=out.rstrip(b"\r\n"),
        stderr=err.rstrip(b"\r\n"),
        changed=True,
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()