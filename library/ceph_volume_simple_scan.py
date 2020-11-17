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
import os


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_volume_simple_scan
short_description: Scan legacy OSD with ceph-volume
version_added: "2.8"
description:
    - Scan legacy OSD with ceph-volume and store the output as JSON file
      in /etc/ceph/osd directory with {OSD_ID}-{OSD_FSID}.json format.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    path:
        description:
            - The OSD directory or metadata partition. The directory or
              partition must exist.
        required: false
    force:
        description:
            - Force re-scanning an OSD and overwriting the JSON content.
        required: false
        default: false
    stdout:
        description:
            - Do not store the output to JSON file but stdout instead.
        required: false
        default: false
author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: scan all running OSDs
  ceph_volume_simple_scan:
    cluster: ceph

- name: scan an OSD with the directory
  ceph_volume_simple_scan:
    cluster: ceph
    path: /var/lib/ceph/osd/ceph-3

- name: scan an OSD with the partition
  ceph_volume_simple_scan:
    cluster: ceph
    path: /dev/sdb1

- name: rescan an OSD and print the result on stdout
  ceph_volume_simple_scan:
    cluster: ceph
    path: /dev/nvme0n1p1
    force: true
    stdout: true
'''

RETURN = '''#  '''


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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=False, default='ceph'),
            path=dict(type='path', required=False),
            force=dict(type='bool', required=False, default=False),
            stdout=dict(type='bool', required=False, default=False),
        ),
        supports_check_mode=True,
    )

    path = module.params.get('path')
    cluster = module.params.get('cluster')
    force = module.params.get('force')
    stdout = module.params.get('stdout')

    if path and not os.path.exists(path):
        module.fail_json(msg='{} does not exist'.format(path), rc=1)

    startd = datetime.datetime.now()

    container_image = os.getenv('CEPH_CONTAINER_IMAGE')
    container_binary = os.getenv('CEPH_CONTAINER_BINARY')
    if container_binary and container_image:
        cmd = [container_binary,
               'run', '--rm', '--privileged',
               '--ipc=host', '--net=host',
               '-v', '/etc/ceph:/etc/ceph:z',
               '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
               '-v', '/var/log/ceph/:/var/log/ceph/:z',
               '-v', '/run/lvm/:/run/lvm/',
               '-v', '/run/lock/lvm/:/run/lock/lvm/',
               '--entrypoint=ceph-volume', container_image]
    else:
        cmd = ['ceph-volume']

    cmd.extend(['--cluster', cluster, 'simple', 'scan'])

    if force:
        cmd.append('--force')

    if stdout:
        cmd.append('--stdout')

    if path:
        cmd.append(path)

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
