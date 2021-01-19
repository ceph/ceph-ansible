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

from ansible.module_utils.basic import AnsibleModule

import datetime
import os

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_disk
short_description: Create ceph OSDs with ceph-disk
description:
    - Using the ceph-disk utility available in Ceph this module
      can be used to create ceph OSDs that are backed by devices.
    - Only available in ceph versions luminous or mimic.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    objectstore:
        description:
            - The objectstore of the OSD, either filestore or bluestore
            - Required if action is 'prepare'
        required: false
        choices: ['bluestore', 'filestore']
        default: bluestore
    action:
        description:
            - The action to take. Either creating OSDs or zapping devices.
        required: true
        choices: ['prepare', 'activate', 'list', 'zap']
        default: prepare
    data:
        description:
            - The device to use for the OSD data.
        required: false
    journal:
        description:
            - The device to use as a filestore journal.
            - Only applicable if objectstore is 'filestore'.
        required: false
    db:
        description:
            - The device to use for bluestore block.db.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    wal:
        description:
            - The device to use for bluestore block.wal.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    dmcrypt:
        description:
            - If set to True the OSD will be encrypted with dmcrypt.
        required: false
author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: set up a filestore osd with a dedicated journal
  ceph_disk:
    objectstore: filestore
    data: /dev/sdb
    journal: /dev/sdc
    action: prepare

- name: set up a dmcrypt bluestore osd
  ceph_disk:
    objectstore: bluestore
    data: /dev/sdb
    dmcrypt: true
    action: prepare

- name: set up a bluestore osd with dedicated devices for block.wal and block.db
  ceph_disk:
    cluster: ceph
    objectstore: bluestore
    data: /dev/sdb
    db: /dev/sdc
    wal: /dev/nvme0n1
    action: prepare

- name: activate an OSD
  ceph_disk:
    data: /dev/sdb1
    action: activate

- name: list all OSDs
  ceph_disk:
    action: list

- name: zap an OSD
  ceph_disk:
    data: /dev/sdb
    action: zap
'''


def container_exec(binary, container_image):
    '''
    Build the docker CLI to run a command inside a container
    '''
    command_exec = ['docker', 'run', '--rm', '--privileged', '--net=host', '--ipc=host',
                    '--ulimit', 'nofile=1024:4096',
                    '-v', '/var/run/udev/:/var/run/udev/:z',
                    '-v', '/dev:/dev', '-v', '/etc/ceph:/etc/ceph:z',
                    '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                    '-v', '/var/log/ceph/:/var/log/ceph/:z',
                    os.path.join('--entrypoint=' + binary),
                    container_image]
    return command_exec


def exec_command(module, cmd):
    '''
    Execute command
    '''

    rc, out, err = module.run_command(cmd)
    return rc, cmd, out, err


def is_containerized():
    '''
    Check if we are running on a containerized cluster
    '''

    if 'CEPH_CONTAINER_IMAGE' in os.environ:
        container_image = os.getenv('CEPH_CONTAINER_IMAGE')
    else:
        container_image = None

    return container_image


def ceph_disk_cmd(subcommand, cluster=None, container_image=None):
    '''
    Build ceph-disk initial command
    '''

    if container_image:
        cmd = container_exec('ceph-disk', container_image)
    else:
        cmd = ['ceph-disk']

    cmd.append(subcommand)

    if cluster:
        cmd.extend(['--cluster', cluster])

    return cmd


def prepare_osd(module, container_image=None):
    '''
    Prepare OSD device
    '''

    cluster = module.params['cluster']
    objectstore = module.params['objectstore']
    data = module.params['data']
    journal = module.params.get('journal', None)
    db = module.params.get('db', None)
    wal = module.params.get('wal', None)
    dmcrypt = module.params.get('dmcrypt', None)

    cmd = ceph_disk_cmd('prepare', cluster, container_image=container_image)
    cmd.append('--{}'.format(objectstore))

    if objectstore == 'filestore':
        cmd.append(data)

        if journal:
            cmd.append(journal)
    else:
        if db:
            cmd.extend(['--block.db', db])

        if wal:
            cmd.extend(['--block.wal', wal])

        cmd.append(data)

    if dmcrypt:
        cmd.append('--dmcrypt')

    return cmd


def activate_osd(module, container_image=None):
    '''
    Activate OSD device
    '''

    data = module.params['data']
    dmcrypt = module.params.get('dmcrypt', None)

    cmd = ceph_disk_cmd('activate', container_image=container_image)

    cmd.append(data)

    if dmcrypt:
        cmd.append('--dmcrypt')

    if container_image:
        cmd.append('--no-start-daemon')

    return cmd


def list_osd(module, container_image=None):
    '''
    List OSD device(s)
    '''

    data = module.params['data']

    cmd = ceph_disk_cmd('list', container_image=container_image)

    if data:
        cmd.append(data)

    return cmd


def zap_osd(module, container_image=None):
    '''
    Zap OSD device(s)
    '''

    data = module.params['data']

    cmd = ceph_disk_cmd('zap', container_image=container_image)

    cmd.append(data)

    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=False, default='ceph'),
            objectstore=dict(type='str', required=False, choices=['bluestore', 'filestore'], default='bluestore'),
            action=dict(type='str', required=False, choices=['prepare', 'activate', 'list', 'zap'], default='prepare'),
            data=dict(type='str', required=False),
            journal=dict(type='str', required=False),
            db=dict(type='str', required=False),
            wal=dict(type='str', required=False),
            dmcrypt=dict(type='bool', required=False, default=False),
        ),
        supports_check_mode=True,
        required_if=[
            ['action', 'prepare', ['cluster', 'data']],
            ['action', 'activate', ['data']],
            ['action', 'zap', ['data']],
        ]
    )

    action = module.params.get('action')

    result = dict(
        changed=False,
        stdout='',
        stderr='',
        rc=0,
        start='',
        end='',
        delta='',
    )

    if module.check_mode:
        module.exit_json(**result)

    startd = datetime.datetime.now()
    changed = False

    container_image = is_containerized()

    if action == 'prepare':
        rc, cmd, out, err = exec_command(module, prepare_osd(module, container_image))
        changed = True

    if action == 'activate':
        rc, cmd, out, err = exec_command(module, activate_osd(module, container_image))
        changed = True

    if action == 'list':
        rc, cmd, out, err = exec_command(module, list_osd(module, container_image))

    if action == 'zap':
        rc, cmd, out, err = exec_command(module, zap_osd(module, container_image))
        changed = True

    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        rc=rc,
        stdout=out.rstrip('\r\n'),
        stderr=err.rstrip('\r\n'),
        changed=changed,
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
