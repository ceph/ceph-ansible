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
module: ceph_key

author: Sebastien Han <seb@redhat.com>

short_description: Manage Cephx key(s)

version_added: "2.6"

description:
    - Manage CephX creation, deletion and updates.
    It can also list and get information about keyring(s).
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    name:
        description:
            - name of the CephX key
        required: true
    state:
        description:
            - If 'present' is used, the module creates a keyring
            with the associated capabilities.
            If 'present' is used and a secret is provided the module
            will always add the key. Which means it will update
            the keyring if the secret changes, the same goes for
            the capabilities.
            If 'absent' is used, the module will simply delete the keyring.
            If 'list' is used, the module will list all the keys and will
            return a json output.
            If 'update' is used, the module will **only** update
            the capabilities of a given keyring.
            If 'info' is used, the module will return in a json format the
            description of a given keyring.
        required: true
        choices: ['present', 'absent', 'list', 'update', 'info']
        default: list
    caps:
        description:
            - CephX key capabilities
        default: None
        required: false
    secret:
        description:
            - keyring's secret value
        required: false
        default: None
    containerized:
        description:
            - Wether or not this is a containerized cluster. The value is
            assigned or not depending on how the playbook runs.
        required: false
        default: None
    import_key:
        description:
            - Wether or not to import the created keyring into Ceph.
            This can be useful for someone that only wants to generate keyrings
            but not add them into Ceph.
        required: false
        default: True
    auid:
        description:
            - Sets the auid (authenticated user id) for the specified keyring
        required: false
        default: None
    dest:
        description:
            - Destination to write the keyring
        required: false
        default: /etc/ceph/
'''

EXAMPLES = '''

keys_to_create:
  - { name: client.key, key: "AQAin8tUUK84ExAA/QgBtI7gEMWdmnvKBzlXdQ==", caps: { mon: "allow rwx", mds: "allow *" } , mode: "0600" }
  - { name: client.cle, caps: { mon: "allow r", osd: "allow *" } , mode: "0600" }

caps:
  mon: "allow rwx"
  mds: "allow *"

- name: create ceph admin key
  ceph_key:
    name: client.admin
    state: present
    secret: AQAin8tU2DsKFBAAFIAzVTzkL3+gtAjjpQiomw==
    auid: 0
    caps:
      mon: allow *
      osd: allow *
      mgr: allow *
      mds: allow
    mode: 0400
    import_key: False

- name: create monitor initial keyring
  ceph_key:
    name: mon.
    state: present
    secret: AQAin8tUMICVFBAALRHNrV0Z4MXupRw4v9JQ6Q==
    caps:
      mon: allow *
    dest: "/var/lib/ceph/tmp/keyring.mon"
    import_key: False

- name: create cephx key
  ceph_key:
    name: "{{ keys_to_create }}"
    state: present
    caps: "{{ caps }}"

- name: create cephx key but don't import it in Ceph
  ceph_key:
    name: "{{ keys_to_create }}"
    state: present
    caps: "{{ caps }}"
    import_key: False

- name: update cephx key
  ceph_key:
    name: "my_key"
    state: update
    caps: "{{ caps }}"

- name: delete cephx key
  ceph_key:
    name: "my_key"
    state: absent

- name: info cephx key
  ceph_key:
    name: "my_key""
    state: info

- name: list cephx keys
  ceph_key:
    state: list
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


def generate_secret():
    '''
    Generate a CephX secret
    '''

    key = os.urandom(16)
    header = struct.pack('<hiih', 1, int(time.time()), 0, len(key))
    secret = base64.b64encode(header + key)

    return secret


def generate_caps(cmd, _type, caps):
    '''
    Generate CephX capabilities list
    '''

    for k, v in caps.iteritems():
        # makes sure someone didn't pass an empty var,
        # we don't want to add an empty cap
        if len(k) == 0:
            continue
        if _type == "ceph-authtool":
            cmd.extend(["--cap"])
        cmd.extend([k, v])

    return cmd


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


def generate_ceph_authtool_cmd(cluster, name, secret, caps, auid, dest, containerized=None):
    '''
    Generate 'ceph-authtool' command line to execute
    '''

    file_destination = os.path.join(
        dest + "/" + cluster + "." + name + ".keyring")

    cmd = [
        'ceph-authtool',
        '--create-keyring',
        file_destination,
        '--name',
        name,
        '--add-key',
        secret,
    ]

    if auid:
        cmd.extend(['--set-uid', auid])

    cmd = generate_caps(cmd, "ceph-authtool", caps)

    if containerized:
        cmd = containerized.split() + cmd

    return cmd


def create_key(module, result, cluster, name, secret, caps, import_key, auid, dest, containerized=None):
    '''
    Create a CephX key
    '''

    file_path = os.path.join(dest + "/" + cluster + "." + name + ".keyring")

    args = [
        'import',
        '-i',
        file_path,
    ]
    cmd_list = []

    if not secret:
        secret = generate_secret()

    cmd_list.append(generate_ceph_authtool_cmd(
        cluster, name, secret, caps, auid, dest, containerized))

    if import_key:
        cmd_list.append(generate_ceph_cmd(cluster, args, containerized))

    return cmd_list


def update_key(cluster, name, caps, containerized=None):
    '''
    Update a CephX key's capabilities
    '''

    cmd_list = []

    args = [
        'caps',
        name,
    ]

    args = generate_caps(args, "ceph", caps)
    cmd_list.append(generate_ceph_cmd(cluster, args, containerized))

    return cmd_list


def delete_key(cluster, name, containerized=None):
    '''
    Delete a CephX key
    '''

    cmd_list = []

    args = [
        'del',
        name,
    ]

    cmd_list.append(generate_ceph_cmd(cluster, args, containerized))

    return cmd_list


def info_key(cluster, name, containerized=None):
    '''
    Get information about a CephX key
    '''

    cmd_list = []

    args = [
        'get',
        name,
        '-f',
        'json',
    ]

    cmd_list.append(generate_ceph_cmd(cluster, args, containerized))

    return cmd_list


def list_keys(cluster, containerized=None):
    '''
    List all CephX keys
    '''

    cmd_list = []

    args = [
        'ls',
        '-f',
        'json',
    ]

    cmd_list.append(generate_ceph_cmd(cluster, args, containerized))

    return cmd_list


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
        supports_check_mode=True,
        add_file_common_args=True,
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

        # We allow 'present' to override any existing key
        # ONLY if a secret is provided
        # if not we skip the creation
        if import_key:
            if rc == 0 and not secret:
                result["stdout"] = "skipped, since {0} already exists, if you want to update a key use 'state: update'".format(
                    name)
                result['rc'] = rc
                module.exit_json(**result)

        rc, cmd, out, err = exec_commands(module, create_key(
            module, result, cluster, name, secret, caps, import_key, auid, dest, containerized))

        file_path = os.path.join(
            dest + "/" + cluster + "." + name + ".keyring")
        file_args = module.load_file_common_arguments(module.params)
        file_args['path'] = file_path
        module.set_fs_attributes_if_different(file_args, False)
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
