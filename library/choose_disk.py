#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import json
import os
import re

DOCUMENTATION = '''
---
module: choose_disk
author: Erwan Velu <erwan@redhat.com>
short_description: Choose disks based on their features
description:
    To be completed
'''

fout = open("/tmp/ansible", "a")


def _equal(left, right):
    return left == right


def _gt(left, right):
    return float(left) > float(right)


def _lt(left, right):
    return float(left) < float(right)


_REGEXP = re.compile(r'^([^(]+)'          # function name
                     r'\(\s*([^,]+)'      # first argument
                     r'(?:\s*,\s*(.+))?'  # remaining optional arguments
                     r'\)$')              # last parenthesis


def convert_units(value):
    ''' Convert units to ease comparaison '''
    value = str(value).lower().strip()
    storage_units = {
            'kb': 1024,
            'kib': 1000,
            'mb': 1024*1024,
            'mib': 1000*1000,
            'gb': 1024*1024*1024,
            'gib': 1000*1000*1000,
            'tb': 1024*1024*1024*1024,
            'tib': 1000*1000*1000*1000,
            'pb': 1024*1024*1024*1024*1024,
            'pib': 1000*1000*1000*1000*1000
    }

    # Units are storage units
    for size in storage_units.keys():
        if value.endswith(size):
            real_value, unit = value.split(" ")
            return str(float(real_value) * storage_units[unit])

    return value


def find_match(physical_disks, lookup_disks):
    ''' Find a set of matching devices in physical_disks
    '''
    matched_devices = {}
    exclude_list = []

    # Inspecting every disk we search for
    for disk in lookup_disks:
        fout.write("Working on %s\n" % disk)
        # Trying to find a match against all physical disks we have
        for physical_disk in physical_disks:
            # Avoid reusing an already matched physical disk
            if physical_disk in exclude_list:
                continue

            current_physical_disk = physical_disks[physical_disk]
            current_lookup = lookup_disks[disk]
            match_count = 0
            # Checking what features are matching
            for feature in current_lookup:
                if feature not in current_physical_disk:
                    continue

                # Default operator is equal
                operator = "_equal"

                # Assign left and right operands
                right = current_lookup[feature]
                left = current_physical_disk[feature]

                # Test if we have anoter operator
                arguments = _REGEXP.search(right)
                if arguments:
                        new_operator = "_" + arguments.group(1)
                        # Check if the associated function exists
                        if new_operator in globals():
                            # and assign operands with the new values
                            operator = new_operator
                            right = arguments.group(2)
                        else:
                            assert("Unsupported %s operator in : %s\n" % (new_operator, right))

                # Let's check if (left <operator> right) is True meaning the match is done
                if globals()[operator](convert_units(left), convert_units(right)):
                    fout.write("  %s : match  %s %s %s\n" % (physical_disk, left, operator, right))
                    match_count = match_count + 1
                    continue
                else:
                    fout.write("  %s : no match  %s %s %s\n" % (physical_disk, left, operator, right))
                    match_count = match_count
                    # nomatch

            # If all the features matched
            if match_count == len(current_lookup):
                fout.write("  full match (%d/%d) for %s\n" % (match_count, len(current_lookup), physical_disk))
                matched_devices[physical_disk] = physical_disks[physical_disk]
                exclude_list.append(physical_disk)
            # We were unable to find all part of the required features
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
        selected_devices[physical_disk]['bdev'] = '/dev/' + physical_disk

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
            final_list[current_index] = physical_disks[physical_disk]
            final_list[current_index]["bdev"] = "%s%s" % (directory, current_index)
        else:
            current_index = physical_disk
            final_list[current_index] = physical_disks[physical_disk]

    return final_list


def fake_device(device_list):
    '''
    In case of legacy block device names, let's create an internal faked
    entry with a 'bdev' entry filled with the actual path. This will be used to
    make a match later on.
    '''
    devices = {}
    count = 0
    for device in device_list.split():
        devices["legacy_%d" % count] = {"bdev": os.path.dirname(device)+"/"+os.path.basename(device)}
        count = count + 1

    return devices


def main():
    module = None
    matched_devices = None
    lookup_disks = None
    disks = "disks"
    legacy = "legacy_disks"

    fields = {
        "facts": {"required": True, "type": "dict"},
        disks: {"required": False, "type": "dict"},
        legacy: {"required": False, "type": "str"},
    }

    module = AnsibleModule(
        argument_spec=fields
    )

    physical_disks = select_only_free_devices(module.params["facts"])

    # The new disks description is preferred over the legacy (/dev/sd) naming
    if module.params[disks]:
        # From the ansible facts, we only keep the disks that doesn't have
        # partitions, transform their device name in a persistent name
        lookup_disks = expand_disks(module.params[disks])
        physical_disks = get_block_devices_persistent_name(physical_disks)
    elif module.params[legacy]:
        # From the ansible facts, we only keep the disks that doesn't have partitions
        # We don't transform into the persistent naming but rather fake the disk
        # definition by creating "bdev" entries to get a feature to match.
        lookup_disks = expand_disks(fake_device(module.params[legacy]))
    else:
        module.fail_json(msg="no 'disks' or 'legacy_disks' variables found in playbook")
        return

    # From the ansible facts, we only keep the disks that doesn't have
    matched_devices = find_match(physical_disks, lookup_disks)

    if len(matched_devices) < len(lookup_disks):
        message = "Could only find %d of the %d expected devices : %s\n" % (len(matched_devices), len(lookup_disks), physical_disks.keys())
        module.fail_json(msg=message)
    else:
        module.exit_json(msg="Success")

if __name__ == '__main__':
        main()
