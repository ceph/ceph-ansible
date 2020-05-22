#!/usr/bin/python3
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


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_pool

author: Guillaume Abrioux <gabrioux@redhat.com>

short_description: Manage Ceph Pools

version_added: "2.8"

description:
    - Manage Ceph pool(s) creation, deletion and updates.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    name:
        description:
            - name of the Ceph pool
        required: true
    state:
        description:
            If 'present' is used, the module creates a pool if it doesn't exist or
            update it if it already exists.
            If 'absent' is used, the module will simply delete the pool.
            If 'list' is used, the module will return all details about the existing pools
            (json formatted).
        required: true
        choices: ['present', 'absent', 'list']
        default: list
    size:
        description:
            - set the replica size of the pool.
        required: false
        default: 3
    min_size:
        description:
            - set the min_size parameter of the pool.
        required: false
        default: default to `osd_pool_default_min_size` (ceph)
    pg_num:
        description:
            - set the pg_num of the pool.
        required: false
        default: default to `osd_pool_default_pg_num` (ceph)
    pgp_num:
        description:
            - set the pgp_num of the pool.
        required: false
        default: default to `osd_pool_default_pgp_num` (ceph)
    pg_autoscale_mode:
        description:
            - set the pg autoscaler on the pool.
        required: false
        default: 'on'
    target_size_ratio:
        description:
            - set the target_size_ratio on the pool
        required: false
        default: None
    pool_type:
        description:
            - set the pool type, either 'replicated' or 'erasure'
        required: false
        default: 'replicated'
    erasure_profile:
        description:
            - When pool_type = 'erasure', set the erasure profile of the pool
        required: false
        default: 'default'
    rule_name:
        description:
            - Set the crush rule name assigned to the pool
        required: false
        default: 'replicated_rule' when pool_type is 'erasure' else None
    expected_num_objects:
        description:
            -   Set the expected_num_objects parameter of the pool.
        required: false
        default: '0'
    application:
        description:
            - Set the pool application on the pool.
        required: false
        default: None
'''

EXAMPLES = '''

pools:
  - { name: foo, size: 3, application: rbd, pool_type: 'replicated', pg_autoscale_mode: 'on' }

- hosts: all
  become: true
  tasks:
    - name: create a pool
      ceph_pool:
        name: "{{ item.name }}"
        state: present
        size: "{{ item.size }}"
        application: "{{ item.application }}"
        pool_type: "{{ item.pool_type }}"
        pg_autoscale_mode: "{{ item.pg_autoscale_mode }}"
      with_items: "{{ pools }}"
'''

RETURN = '''#  '''

from ansible.module_utils.basic import AnsibleModule  # noqa E402
import datetime  # noqa E402
import json  # noqa E402
import os  # noqa E402
import stat  # noqa E402
import time  # noqa E402



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
    if container_image:
        binary = 'ceph'
        cmd = container_exec(
            binary, container_image)
    else:
        binary = ['ceph']
        cmd = binary

    return cmd

def generate_ceph_cmd(cluster, args, user, user_key, container_image=None):
    '''
    Generate 'ceph' command line to execute
    '''

    cmd = pre_generate_ceph_cmd(container_image=container_image)

    base_cmd = [
        '-n',
        user,
        '-k',
        user_key,
        '--cluster',
        cluster,
        'osd',
        'pool'
    ]

    cmd.extend(base_cmd + args)

    return cmd


def exec_commands(module, cmd):
    '''
    Execute command(s)
    '''

    rc, out, err = module.run_command(cmd)

    return rc, cmd, out, err

def check_pool_exist(cluster, name, user, user_key, output_format='json', container_image=None):
    '''
    Check if a given pool exists
    '''

    args = [ 'stats', name, '-f', output_format ]

    cmd = generate_ceph_cmd(cluster=cluster, args=args, user=user, user_key=user_key, container_image=container_image)

    return cmd


def generate_get_config_cmd(param, cluster, user, user_key, container_image=None):
    _cmd = pre_generate_ceph_cmd(container_image=container_image)
    args = [
        '-n',
        user,
        '-k',
        user_key,
        '--cluster',
        cluster,
        'config',
        'get',
        'mon.*',
        param
    ]
    cmd = _cmd + args
    return cmd


def get_default_running_config(module, cluster, user, user_key, output_format='json', container_image=None):
    '''
    Get some default values set in the cluster
    '''

    params = ['osd_pool_default_size', 'osd_pool_default_min_size', 'osd_pool_default_pg_num', 'osd_pool_default_pgp_num']

    default_running_values = {}

    for param in params:
        rc, cmd, out, err = exec_commands(module, generate_get_config_cmd(param, cluster, user, user_key, container_image=container_image))

        if rc == 0:
            default_running_values[param] = out.strip()
        else:
            return rc, cmd, out, err

    return rc, cmd, default_running_values, err


def get_application_pool(cluster, name, user, user_key, output_format='json', container_image=None):
    '''
    Get application type enabled on a given pool
    '''


    args = [ 'application', 'get', name, '-f', output_format ]

    cmd = generate_ceph_cmd(cluster=cluster, args=args, user=user, user_key=user_key, container_image=container_image)

    return cmd


def enable_application_pool(cluster, name, application, user, user_key, container_image=None):
    '''
    Enable application on a given pool
    '''


    args = [ 'application', 'enable', name, application ]

    cmd = generate_ceph_cmd(cluster=cluster, args=args, user=user, user_key=user_key, container_image=container_image)

    return cmd


def disable_application_pool(cluster, name, application, user, user_key, container_image=None):
    '''
    Disable application on a given pool
    '''

    args = [ 'application', 'disable', name, application, '--yes-i-really-mean-it' ]

    cmd = generate_ceph_cmd(cluster=cluster, args=args, user=user, user_key=user_key, container_image=container_image)

    return cmd


def get_pool_details(module, cluster, name, user, user_key, output_format='json', container_image=None):
    '''
    Get details about a given pool
    '''

    args = [ 'ls', 'detail', '-f', output_format ]

    cmd = generate_ceph_cmd(cluster=cluster, args=args, user=user, user_key=user_key, container_image=container_image)

    rc, cmd, out, err = exec_commands(module, cmd)

    if rc == 0:
        out = [p for p in json.loads(out.strip()) if p['pool_name'] == name][0]

    _rc, _cmd, application_pool, _err = exec_commands(module, get_application_pool(cluster, name, user, user_key, container_image=container_image))

    application = list(json.loads(application_pool.strip()).keys())

    if len(application) == 0:
        out['application'] = ''
    else:
        out['application'] = application[0]

    return rc, cmd, out, err


def compare_pool_config(user_pool_config, running_pool_details):
    '''
    Compare user input config pool details with current running pool details
    '''

    delta = {}
    filter_keys = [ 'pg_num', 'pg_placement_num', 'size', 'pg_autoscale_mode']
    for key in filter_keys:
        if str(running_pool_details[key]) != user_pool_config[key]['value']:
            delta[key] = user_pool_config[key]

    if str(running_pool_details['options'].get('target_size_ratio')) != user_pool_config['target_size_ratio']['value'] and user_pool_config['target_size_ratio']['value'] != None:
        delta['target_size_ratio'] = user_pool_config['target_size_ratio']

    if running_pool_details['application'] != user_pool_config['application']['value'] and user_pool_config['application']['value'] != None:
        delta['application'] = {}
        delta['application']['new_application'] = user_pool_config['application']['value']
        # to be improved (for update_pools()...)
        delta['application']['value'] = delta['application']['new_application']
        delta['application']['old_application'] = running_pool_details['application']

    return delta


def list_pools(cluster, user, user_key, details, output_format='json', container_image=None):
    '''
    List existing pools
    '''

    args = [ 'ls' ]

    if details:
        args.append('detail')

    args.extend([ '-f', output_format ])

    cmd = generate_ceph_cmd(cluster=cluster, args=args, user=user, user_key=user_key, container_image=container_image)

    return cmd


def create_pool(cluster, name, user, user_key, user_pool_config, container_image=None):
    '''
    Create a new pool
    '''

    args = [ 'create', user_pool_config['pool_name']['value'], '--pg_num', user_pool_config['pg_num']['value'], '--pgp_num', user_pool_config['pgp_num']['value'], user_pool_config['type']['value'] ]

    if user_pool_config['type']['value'] == 'replicated':
        args.extend([ user_pool_config['crush_rule']['value'], '--expected_num_objects', user_pool_config['expected_num_objects']['value'], '--size', user_pool_config['size']['value'], '--autoscale-mode', user_pool_config['pg_autoscale_mode']['value'] ])

    elif user_pool_config['type']['value'] == 'erasure':
        args.extend([ user_pool_config['erasure_profile']['value'] ])

        if user_pool_config['crush_rule']['value'] != None:
            args.extend([ user_pool_config['crush_rule']['value'] ])

        args.extend([ '--expected_num_objects', user_pool_config['expected_num_objects']['value'] , '--autoscale-mode', user_pool_config['pg_autoscale_mode']['value']])

    cmd = generate_ceph_cmd(cluster=cluster, args=args, user=user, user_key=user_key, container_image=container_image)

    return cmd


def remove_pool(cluster, name, user, user_key, container_image=None):
    '''
    Remove a pool
    '''

    args = [ 'rm', name, name, '--yes-i-really-really-mean-it']

    cmd = generate_ceph_cmd(cluster=cluster, args=args, user=user, user_key=user_key, container_image=container_image)

    return cmd


def update_pool(module, cluster, name, user, user_key, delta, container_image=None):
    '''
    Update an existing pool
    '''

    report = ""

    for key in delta.keys():
        if key != 'application':
            args = [ 'set', name, delta[key]['cli_set_opt'], delta[key]['value'] ]

            cmd = generate_ceph_cmd(cluster=cluster, args=args, user=user, user_key=user_key, container_image=container_image)

            rc, cmd, out, err = exec_commands(module, cmd)
            if rc != 0:
                return rc, cmd, out, err

        else:
            rc, cmd, out, err = exec_commands(module, disable_application_pool(cluster, name, delta['application']['old_application'], user, user_key, container_image=container_image))
            if rc != 0:
                return rc, cmd, out, err

            rc, cmd, out, err = exec_commands(module, enable_application_pool(cluster, name, delta['application']['new_application'], user, user_key, container_image=container_image))
            if rc != 0:
                return rc, cmd, out, err

        report = report + "\n" + "{} has been updated: {} is now {}".format(name, key, delta[key]['value'])

    out = report
    return rc, cmd, out, err


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
        state=dict(type='str', required=True, choices=['present', 'absent', 'list']),
        details=dict(type='bool', required=False, default=False),
        size=dict(type='str', required=False),
        min_size=dict(type='str', required=False),
        pg_num=dict(type='str', required=False, default=None),
        pgp_num=dict(type='str', required=False, default=None),
        pg_autoscale_mode=dict(type='str', required=False, default='on'),
        target_size_ratio=dict(type='str', required=False, default=None),
        pool_type=dict(type='str', required=False, default='replicated', choices=['replicated', 'erasure', '1', '3']),
        erasure_profile=dict(type='str', required=False, default='default'),
        rule_name=dict(type='str', required=False, default=None),
        expected_num_objects=dict(type='str', required=False, default="0"),
        application=dict(type='str', required=False, default=None),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        add_file_common_args=True,
    )

    # Gather module parameters in variables
    cluster = module.params.get('cluster')
    name = module.params.get('name')
    state = module.params.get('state')
    details = module.params.get('details')
    pg_num = module.params.get('pg')
    pgp_num = module.params.get('pgp')
    pg_autoscale_mode = module.params.get('pg_autoscale_mode')
    target_size_ratio = module.params.get('target_size_ratio')
    application = module.params.get('application')

    if module.params.get('pg_autoscale_mode').lower() in ['true', 'on', 'yes']:
        pg_autoscale_mode = 'on'
    elif module.params.get('pg_autoscale_mode').lower() in ['false', 'off', 'no']:
        pg_autoscale_mode = 'off'
    else:
        pg_autoscale_mode = 'warn'

    if module.params.get('pool_type') == '1':
        pool_type = 'replicated'
    elif module.params.get('pool_type') == '3':
        pool_type = 'erasure'
    else:
        pool_type = module.params.get('pool_type')

    if module.params.get('rule_name') == None:
        rule_name = 'replicated_rule' if pool_type == 'replicated' else None
    else:
        rule_name = module.params.get('rule_name')

    erasure_profile = module.params.get('erasure_profile')
    expected_num_objects = module.params.get('expected_num_objects')



    user_pool_config = {
        'pool_name': { 'value': name },
        'pg_num': { 'value': pg_num, 'cli_set_opt': 'pg_num' },
        'pgp_num': { 'value': pgp_num, 'cli_set_opt': 'pgp_num' },
        'pg_autoscale_mode': { 'value': pg_autoscale_mode, 'cli_set_opt': 'pg_autoscale_mode' },
        'target_size_ratio': { 'value': target_size_ratio, 'cli_set_opt': 'target_size_ratio' },
        'application': {'value': application },
        'type': { 'value': pool_type },
        'erasure_profile': { 'value': erasure_profile },
        'crush_rule': { 'value': rule_name, 'cli_set_opt': 'crush_rule' },
        'expected_num_objects': { 'value': expected_num_objects }
    }

    if module.check_mode:
        return dict(
            changed=False,
            stdout='',
            stderr='',
            rc='',
            start='',
            end='',
            delta='',
        )

    startd = datetime.datetime.now()
    changed = False

    # will return either the image name or None
    container_image = is_containerized()

    user = "client.admin"
    keyring_filename = cluster + '.' + user + '.keyring'
    user_key = os.path.join("/etc/ceph/", keyring_filename)

    def_opt = {
        'size': {
            'conf_name': 'osd_pool_default_size',
            'cli_set_opt': 'size'
        },
        'min_size': {
            'conf_name': 'osd_pool_default_min_size',
            'cli_set_opt': 'min_size'
        },
        'pg_num': {
            'conf_name': 'osd_pool_default_pg_num',
            'cli_set_opt': 'pg_num'
        },
        'pgp_num': {
            'conf_name': 'osd_pool_default_pgp_num',
            'cli_set_opt': 'pgp_num'
        }
    }

    if state == "present":
        rc, cmd, default_running_ceph_config, err = get_default_running_config(module, cluster, user, user_key, container_image=container_image)
        if rc == 0:
            for k, v in def_opt.items():
                if module.params[k] == None:
                    user_pool_config[k] = {'value': default_running_ceph_config[v['conf_name']], 'cli_set_opt': v['cli_set_opt']}
                else:
                    user_pool_config[k] = {'value': module.params.get(k), 'cli_set_opt': v['cli_set_opt']}
            rc, cmd, out, err = exec_commands(module, check_pool_exist(cluster, name, user, user_key, container_image=container_image))
            if rc == 0:
                running_pool_details = get_pool_details(module, cluster, name, user, user_key, container_image=container_image)
                user_pool_config['pg_placement_num'] = { 'value': str(running_pool_details[2]['pg_placement_num']), 'cli_set_opt': 'pgp_num' }
                delta = compare_pool_config(user_pool_config, running_pool_details[2])
                if len(delta) > 0 and running_pool_details[2]['erasure_code_profile'] == "" and 'size' not in delta.keys():
                    rc, cmd, out, err = update_pool(module, cluster, name, user, user_key, delta, container_image=container_image)
                    if rc == 0:
                        changed = True
                else:
                    out = "Pool {} already exists and there is nothing to update.".format(name)
            else:
                rc, cmd, out, err = exec_commands(module, create_pool(cluster, name, user, user_key, user_pool_config=user_pool_config, container_image=container_image))
                if user_pool_config['application']['value'] != None:
                    _rc, _cmd, _out, _err = exec_commands(module, enable_application_pool(cluster, name, user_pool_config['application']['value'], user, user_key, container_image=container_image))
                changed = True

    elif state == "list":
        rc, cmd, out, err = exec_commands(module, list_pools(cluster, name, user, user_key, details, container_image=container_image))
        if rc != 0:
            out = "Couldn't list pool(s) present on the cluster"

    elif state == "absent":
        rc, cmd, out, err = exec_commands(module, remove_pool(cluster, name, user, user_key, container_image=container_image))


    exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=changed)


def main():
    run_module()


if __name__ == '__main__':
    main()

