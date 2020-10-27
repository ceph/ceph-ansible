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
module: ceph_fs

short_description: Manage Ceph File System

version_added: "2.8"

description:
    - Manage Ceph File System(s) creation, deletion and updates.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    name:
        description:
            - name of the Ceph File System.
        required: true
    state:
        description:
            If 'present' is used, the module creates a filesystem if it
            doesn't  exist or update it if it already exists.
            If 'absent' is used, the module will simply delete the filesystem.
            If 'info' is used, the module will return all details about the
            existing filesystem (json formatted).
        required: false
        choices: ['present', 'absent', 'info']
        default: present
    data:
        description:
            - name of the data pool.
        required: false
    metadata:
        description:
            - name of the metadata pool.
        required: false
    max_mds:
        description:
            - name of the max_mds attribute.
        required: false


author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: create a Ceph File System
  ceph_fs:
    name: foo
    data: bar_data
    metadata: bar_metadata
    max_mds: 2

- name: get a Ceph File System information
  ceph_fs:
    name: foo
    state: info

- name: delete a Ceph File System
  ceph_fs:
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


def pre_generate_ceph_cmd(container_image=None):
    '''
    Generate ceph prefix comaand
    '''
    if container_image:
        cmd = container_exec('ceph', container_image)
    else:
        cmd = ['ceph']

    return cmd


def generate_ceph_cmd(cluster, args, container_image=None):
    '''
    Generate 'ceph' command line to execute
    '''

    cmd = pre_generate_ceph_cmd(container_image=container_image)

    base_cmd = [
        '--cluster',
        cluster,
        'fs'
    ]

    cmd.extend(base_cmd + args)

    return cmd


def exec_commands(module, cmd):
    '''
    Execute command(s)
    '''

    rc, out, err = module.run_command(cmd)

    return rc, cmd, out, err


def create_fs(module, container_image=None):
    '''
    Create a new fs
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    data = module.params.get('data')
    metadata = module.params.get('metadata')

    args = ['new', name, metadata, data]

    cmd = generate_ceph_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image)

    return cmd


def get_fs(module, container_image=None):
    '''
    Get existing fs
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['get', name, '--format=json']

    cmd = generate_ceph_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image)

    return cmd


def remove_fs(module, container_image=None):
    '''
    Remove a fs
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['rm', name, '--yes-i-really-mean-it']

    cmd = generate_ceph_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image)

    return cmd


def fail_fs(module, container_image=None):
    '''
    Fail a fs
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')

    args = ['fail', name]

    cmd = generate_ceph_cmd(cluster=cluster,
                            args=args,
                            container_image=container_image)

    return cmd


def set_fs(module, container_image=None):
    '''
    Set parameter to a fs
    '''

    cluster = module.params.get('cluster')
    name = module.params.get('name')
    max_mds = module.params.get('max_mds')

    args = ['set', name, 'max_mds', str(max_mds)]

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
        data=dict(type='str', required=False),
        metadata=dict(type='str', required=False),
        max_mds=dict(type='int', required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[['state', 'present', ['data', 'metadata']]],
    )

    # Gather module parameters in variables
    name = module.params.get('name')
    state = module.params.get('state')
    max_mds = module.params.get('max_mds')

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
        rc, cmd, out, err = exec_commands(module, get_fs(module, container_image=container_image))  # noqa: E501
        if rc == 0:
            fs = json.loads(out)
            if max_mds and fs["mdsmap"]["max_mds"] != max_mds:
                rc, cmd, out, err = exec_commands(module, set_fs(module, container_image=container_image))  # noqa: E501
                if rc == 0:
                    changed = True
        else:
            rc, cmd, out, err = exec_commands(module, create_fs(module, container_image=container_image))  # noqa: E501
            if max_mds and max_mds > 1:
                exec_commands(module, set_fs(module, container_image=container_image))  # noqa: E501
            if rc == 0:
                changed = True

    elif state == "absent":
        rc, cmd, out, err = exec_commands(module, get_fs(module, container_image=container_image))  # noqa: E501
        if rc == 0:
            exec_commands(module, fail_fs(module, container_image=container_image))  # noqa: E501
            rc, cmd, out, err = exec_commands(module, remove_fs(module, container_image=container_image))  # noqa: E501
            if rc == 0:
                changed = True
        else:
            rc = 0
            out = "Ceph File System {} doesn't exist".format(name)

    elif state == "info":
        rc, cmd, out, err = exec_commands(module, get_fs(module, container_image=container_image))  # noqa: E501

    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)  # noqa: E501


def main():
    run_module()


if __name__ == '__main__':
    main()
