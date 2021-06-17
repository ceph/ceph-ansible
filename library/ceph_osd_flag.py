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
import os
import datetime


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_osd_flag
short_description: Manage Ceph OSD flag
version_added: "2.8"
description:
    - Manage Ceph OSD flag
options:
    name:
        description:
            - name of the ceph OSD flag.
        required: true
        choices: ['noup', 'nodown', 'noout', 'nobackfill', 'norebalance',
                 'norecover', 'noscrub', 'nodeep-scrub']
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    state:
        description:
            - If 'present' is used, the module sets the OSD flag.
            If 'absent' is used, the module will unset the OSD flag.
        required: false
        choices: ['present', 'absent']
        default: present
author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: set noup OSD flag
  ceph_osd_flag:
    name: noup

- name: unset multiple OSD flags
  ceph_osd_flag:
    name: '{{ item }}'
    state: absent
  loop:
    - 'noup'
    - 'norebalance'
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


def generate_ceph_cmd(sub_cmd, args, user_key=None, cluster='ceph', user='client.admin', container_image=None):
    '''
    Generate 'ceph' command line to execute
    '''

    if not user_key:
        user_key = '/etc/ceph/{}.{}.keyring'.format(cluster, user)

    cmd = pre_generate_ceph_cmd(container_image=container_image)

    base_cmd = [
        '-n',
        user,
        '-k',
        user_key,
        '--cluster',
        cluster
    ]
    base_cmd.extend(sub_cmd)
    cmd.extend(base_cmd + args)

    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, choices=['noup', 'nodown', 'noout', 'nobackfill', 'norebalance', 'norecover', 'noscrub', 'nodeep-scrub']),  # noqa: E501
            cluster=dict(type='str', required=False, default='ceph'),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),  # noqa: E501
        ),
        supports_check_mode=True,
    )

    name = module.params.get('name')
    cluster = module.params.get('cluster')
    state = module.params.get('state')

    startd = datetime.datetime.now()

    container_image = is_containerized()

    if state == 'present':
        cmd = generate_ceph_cmd(['osd', 'set'], [name], cluster=cluster, container_image=container_image)  # noqa: E501
    else:
        cmd = generate_ceph_cmd(['osd', 'unset'], [name], cluster=cluster, container_image=container_image)  # noqa: E501

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
