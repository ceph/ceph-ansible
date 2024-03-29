#!/usr/bin/python

# Copyright (c) 2018 Red Hat, Inc.
#
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.ca_common import fatal
except ImportError:
    from module_utils.ca_common import fatal
import datetime

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
        return sorted(location, key=lambda crush: crush_bucket_types.index(crush[0]))  # noqa: E501
    except ValueError as error:
        fatal("{} is not a valid CRUSH bucket, valid bucket types are {}".format(error.args[0].split()[0], crush_bucket_types), module)  # noqa: E501


def get_crush_tree(module, cluster, containerized=None):
    '''
    Get the CRUSH map
    '''
    cmd = [
        'ceph',
        '--cluster',
        cluster,
        'osd',
        'crush',
        'tree',
        '--format',
        'json',
    ]
    if containerized:
        cmd = containerized.split() + cmd

    rc, out, err = module.run_command(cmd)
    return rc, cmd, out, err


def create_and_move_buckets_list(cluster, location, crush_map, containerized=None):  # noqa: E501
    '''
    Creates Ceph CRUSH buckets and arrange the hierarchy
    '''
    def bucket_exists(bucket_name, bucket_type):
        for item in crush_map['nodes']:
            if item['name'] == bucket_name and item['type'] == bucket_type:
                return True
        return False

    def bucket_in_place(bucket_name, target_bucket_name, target_bucket_type):  # noqa: E501
        bucket_id = None
        target_bucket = None
        for item in crush_map['nodes']:
            if item['name'] == bucket_name:
                bucket_id = item['id']
            if item['name'] == target_bucket_name and item['type'] == target_bucket_type:  # noqa: E501
                target_bucket = item

        if not bucket_id or not target_bucket:
            return False

        return bucket_id in target_bucket['children']

    previous_bucket = None
    cmd_list = []
    for item in location:
        bucket_type, bucket_name = item
        # ceph osd crush add-bucket maroot root
        if not bucket_exists(bucket_name, bucket_type):
            cmd_list.append(generate_cmd(cluster, "add-bucket", bucket_name, bucket_type, containerized))  # noqa: E501
        if previous_bucket:
            # ceph osd crush move monrack root=maroot
            if not bucket_in_place(previous_bucket, bucket_name, bucket_type):  # noqa: E501
                cmd_list.append(generate_cmd(cluster, "move", previous_bucket, "%s=%s" % (bucket_type, bucket_name), containerized))  # noqa: E501
        previous_bucket = item[1]
    return cmd_list


def exec_commands(module, cmd_list):
    '''
    Creates Ceph commands
    '''
    for cmd in cmd_list:
        rc, out, err = module.run_command(cmd)
    return rc, cmd, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=False, default='ceph'),
            location=dict(type='dict', required=True),
            containerized=dict(type='str', required=False, default=None),
        ),
        supports_check_mode=True,
    )

    cluster = module.params['cluster']
    location_dict = module.params['location']
    location = sort_osd_crush_location(tuple(location_dict.items()), module)
    containerized = module.params['containerized']

    diff = dict(before="", after="")
    startd = datetime.datetime.now()

    # get the CRUSH map
    rc, cmd, out, err = get_crush_tree(module, cluster, containerized)
    if rc != 0 and not module.check_mode:
        module.fail_json(msg='non-zero return code', rc=rc, stdout=out, stderr=err)  # noqa: E501

    # parse the JSON output
    if rc == 0:
        crush_map = module.from_json(out)
    else:
        crush_map = {"nodes": []}

    # run the Ceph command to add buckets
    cmd_list = create_and_move_buckets_list(cluster, location, crush_map, containerized)  # noqa: E501

    changed = len(cmd_list) > 0
    if changed:
        diff['after'] = module.jsonify(cmd_list)
        if not module.check_mode:
            rc, cmd, out, err = exec_commands(module, cmd_list)  # noqa: E501

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
        diff=diff
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
