#!/usr/bin/python

#
# Copyright (c) 2018 Red Hat, Inc.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_crush

author: Sebastien Han <seb@redhat.com>

short_description: Create Ceph CRUSH hierarchy

version_added: "2.6"

description:
    - By using the hostvar variable 'osd_crush_location'
    ceph_crush creates buckets and places them in the right CRUSH hierarchy

options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    location:
        description:
            - osd_crush_location dict from the inventory file. It contains
            the placement of each host in the CRUSH map.
        required: true
    containerized:
        description:
            - Weither or not this is a containerized cluster. The value is
            assigned or not depending on how the playbook runs.
        required: false
        default: None
'''

EXAMPLES = '''
- name: configure crush hierarchy
  ceph_crush:
    cluster: "{{ cluster }}"
    location: "{{ hostvars[item]['osd_crush_location'] }}"
    containerized: "{{ container_exec_cmd }}"
  with_items: "{{ groups[osd_group_name] }}"
  when: crush_rule_config | bool
'''

RETURN = '''#  '''

from ansible.module_utils.basic import AnsibleModule
import datetime


def fatal(message, module):
    '''
    Report a fatal error and exit
    '''
    if module:
        module.fail_json(msg=message, rc=1)
    else:
        raise(Exception(message))


def generate_cmd(cluster, subcommand, bucket, bucket_type, containerized=None):
    '''
    Generate command line to execute
    '''
    cmd = [
        'ceph',
        '--cluster',
        cluster,
        'osd',
        'crush',
        subcommand,
        bucket,
        bucket_type,
    ]
    if containerized:
        cmd = containerized.split() + cmd
    return cmd


def sort_osd_crush_location(location, module):
    '''
    Sort location tuple
    '''
    if len(location) < 2:
        fatal("You must specify at least 2 buckets.", module)

    if not any(item for item in location if item[0] == "host"):
        fatal("You must specify a 'host' bucket.", module)

    try:
        crush_bucket_types = [
            "host",
            "chassis",
            "rack",
            "row",
            "pdu",
            "pod",
            "room",
            "datacenter",
            "region",
            "root",
        ]
        return sorted(location, key=lambda crush: crush_bucket_types.index(crush[0]))
    except ValueError as error:
        fatal("{} is not a valid CRUSH bucket, valid bucket types are {}".format(error.args[0].split()[0], crush_bucket_types), module)


def create_and_move_buckets_list(cluster, location, containerized=None):
    '''
    Creates Ceph CRUSH buckets and arrange the hierarchy
    '''
    previous_bucket = None
    cmd_list = []
    for item in location:
        bucket_type, bucket_name = item
        # ceph osd crush add-bucket maroot root
        cmd_list.append(generate_cmd(cluster, "add-bucket", bucket_name, bucket_type, containerized))
        if previous_bucket:
            # ceph osd crush move monrack root=maroot
            cmd_list.append(generate_cmd(cluster, "move", previous_bucket, "%s=%s" % (bucket_type, bucket_name), containerized))
        previous_bucket = item[1]
    return cmd_list


def exec_commands(module, cmd_list):
    '''
    Creates Ceph commands
    '''
    for cmd in cmd_list:
        rc, out, err = module.run_command(cmd)
    return rc, cmd, out, err


def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        location=dict(type='dict', required=True),
        containerized=dict(type='str', required=True, default=None),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    cluster = module.params['cluster']
    location_dict = module.params['location']
    location = sort_osd_crush_location(tuple(location_dict.items()), module)
    containerized = module.params['containerized']

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

    # run the Ceph command to add buckets
    rc, cmd, out, err = exec_commands(module, create_and_move_buckets_list(cluster, location, containerized))

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
        changed=True,
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
