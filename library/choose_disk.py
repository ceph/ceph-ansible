#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import json
import os

DOCUMENTATION = '''
---
module: choose_disk
author: Erwan Velu <erwan@redhat.com>
short_description: Choose disks based on their features
description:
    To be completed
'''

fout = open("/tmp/ansible", "a")


def find_match(physical_disks, lookup_disks):
    ''' Find a set of matching devices in physical_disks
    '''
    matched_devices = {}
    exclude_list = []
    for disk in lookup_disks:
        fout.write("Working on %s\n" % disk)
        for physical_disk in physical_disks:
            if physical_disk in exclude_list:
                fout.write("Skipping %s as per the exclude list\n" % physical_disk)
                continue
            current_physical_disk = physical_disks[physical_disk]
            current_lookup = lookup_disks[disk]
            match_count = 0
            for feature in current_lookup:
                if feature not in current_physical_disk:
                    continue
                elif current_lookup[feature] != current_physical_disk[feature]:
                    match_count = match_count
                    # nomatch
                else:
                    fout.write("  %s : match for %s\n" % (physical_disk, feature))
                    match_count = match_count + 1
                    continue

            if match_count == len(current_lookup):
                fout.write("  full match (%d/%d) for %s\n" % (match_count, len(current_lookup), physical_disk))
                matched_devices[physical_disk] = physical_disks[physical_disk]
                exclude_list.append(physical_disk)
            elif match_count > 0:
                fout.write("  partial match for %s with %d/%d\n" % (physical_disk, match_count, len(current_lookup)))
            else:
                fout.write("  no match for %s\n" % (physical_disk))

    return matched_devices


def expand_disks(lookup_disks):
    '''
    Read the disks structure and expand them according to the count directive
    If no count is provided, a default value of 1 is taken.
    '''
    final_list = {}
    for disk in lookup_disks:
        count = 0
        if 'count' not in lookup_disks[disk]:
            count = 1
        if 'count' in lookup_disks[disk]:
            count = int(lookup_disks[disk]['count'])
            del lookup_disks[disk]['count']

        for n in range(0, count, 1):
            final_list["%s_%d" % (disk, n)] = lookup_disks[disk]

    return final_list


def select_only_free_devices(physical_disks):
    ''' Don't keep that have partitions '''
    selected_devices = {}
    for physical_disk in physical_disks:
        current_physical_disk = physical_disks[physical_disk]

        # Don't consider devices that doesn't have partitions
        if 'partitions' not in current_physical_disk:
            continue
        # Don't consider the device if partition list is not empty,
        if len(current_physical_disk['partitions']) > 0:
            continue

        selected_devices[physical_disk] = physical_disks[physical_disk]

    return selected_devices


def get_block_devices_persistent_name(physical_disks):
    ''' Replace the short name (sda) by the persistent naming 'by-id' '''
    directory = "/dev/disk/by-id/"

    # If the directory doesn't exist, reports the list as-is
    if not os.path.isdir(directory):
        return physical_disks

    final_list = {}
    matching_list = {}
    for f in os.listdir(directory):
        device_name = os.readlink(directory + f).split("/")[-1]
        if device_name in physical_disks:
            if device_name not in matching_list:
                matching_list[device_name] = [f]
            else:
                matching_list[device_name].append(f)

    for physical_disk in physical_disks:
        if physical_disk in matching_list:
            current_index = sorted(matching_list[physical_disk])[0]
        else:
            current_index = physical_disk

        final_list[current_index] = physical_disks[physical_disk]
        final_list[current_index]["prefix"] = "%s" % (directory)

    return final_list

def main():
    fields = {
        "facts": {"required": False, "type": "dict"},
        "disks": {"required": True, "type": "dict"},
    }

    module = AnsibleModule(
        argument_spec=fields
    )

    physical_disks = module.params["facts"]
    lookup_disks = expand_disks(module.params["disks"])

    matched_devices = find_match(physical_disks, lookup_disks)

    if len(matched_devices) < len(lookup_disks):
        message = module.fail_json(msg="Could only find %d of the %d expected devices \n" % (len(matched_devices), len(lookup_disks)))
        fout.write(message)
        module.fail_json(msg=message)
    else:
        module.exit_json(msg="Success")

if __name__ == '__main__':
        main()
