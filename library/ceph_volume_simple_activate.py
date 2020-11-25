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
import os


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_volume_simple_activate
short_description: Activate legacy OSD with ceph-volume
version_added: "2.8"
description:
    - Activate legacy OSD with ceph-volume by providing the JSON file from
      the scan operation or by passing the OSD ID and OSD FSID.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    path:
        description:
            - The OSD metadata as JSON file in /etc/ceph/osd directory, it
              must exist.
        required: false
    osd_id:
        description:
            - The legacy OSD ID.
        required: false
    osd_fsid:
        description:
            - The legacy OSD FSID.
        required: false
    osd_all:
        description:
            - Activate all legacy OSDs.
        required: false
    systemd:
        description:
            - Using systemd unit during the OSD activation.
        required: false
        default: true
author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: activate all legacy OSDs
  ceph_volume_simple_activate:
    cluster: ceph
    osd_all: true

- name: activate a legacy OSD via OSD ID and OSD FSID
  ceph_volume_simple_activate:
    cluster: ceph
    osd_id: 3
    osd_fsid: 0c4a7eca-0c2a-4c12-beff-08a80f064c52

- name: activate a legacy OSD via the JSON file
  ceph_volume_simple_activate:
    cluster: ceph
    path: /etc/ceph/osd/3-0c4a7eca-0c2a-4c12-beff-08a80f064c52.json

- name: activate a legacy OSD via the JSON file without systemd
  ceph_volume_simple_activate:
    cluster: ceph
    path: /etc/ceph/osd/3-0c4a7eca-0c2a-4c12-beff-08a80f064c52.json
    systemd: false
'''

RETURN = '''#  '''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=False, default='ceph'),
            path=dict(type='path', required=False),
            systemd=dict(type='bool', required=False, default=True),
            osd_id=dict(type='str', required=False),
            osd_fsid=dict(type='str', required=False),
            osd_all=dict(type='bool', required=False),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ('osd_all', 'osd_id'),
            ('osd_all', 'osd_fsid'),
            ('path', 'osd_id'),
            ('path', 'osd_fsid'),
        ],
        required_together=[
            ('osd_id', 'osd_fsid')
        ],
        required_one_of=[
            ('path', 'osd_id', 'osd_all'),
            ('path', 'osd_fsid', 'osd_all'),
        ],
    )

    path = module.params.get('path')
    cluster = module.params.get('cluster')
    systemd = module.params.get('systemd')
    osd_id = module.params.get('osd_id')
    osd_fsid = module.params.get('osd_fsid')
    osd_all = module.params.get('osd_all')

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

    cmd.extend(['--cluster', cluster, 'simple', 'activate'])

    if osd_all:
        cmd.append('--all')
    else:
        if path:
            cmd.extend(['--file', path])
        else:
            cmd.extend([osd_id, osd_fsid])

    if not systemd:
        cmd.append('--no-systemd')

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
