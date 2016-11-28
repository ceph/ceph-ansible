#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import json
import logging
import os
import re
import subprocess

DOCUMENTATION = '''
---
module: choose_disk
author: Erwan Velu <erwan@redhat.com>
short_description: Choose disks based on their features
description:
    To be completed
'''

logger = logging.getLogger('choose_disk')
module = None


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

    logger.info("Looking for matches")
    # Inspecting every disk we search for
    for disk in sorted(lookup_disks):

        current_lookup = lookup_disks[disk]
        infinite = False
        if "infinite" in current_lookup.keys():
            infinite = True
            del current_lookup["infinite"]

        if len(exclude_list) == len(physical_disks):
            info(" Skipping %s as no more free devices to match" % (disk))
            continue

        logger.info(" Inspecting %s" % disk)
        # Trying to find a match against all physical disks we have
        for physical_disk in sorted(physical_disks):
            # Avoid reusing an already matched physical disk
            if physical_disk in exclude_list:
                continue

            current_physical_disk = physical_disks[physical_disk]
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
                            fatal("Unsupported %s operator in : %s" % (new_operator, right))

                # Let's check if (left <operator> right) is True meaning the match is done
                if globals()[operator](convert_units(left), convert_units(right)):
                    debug("  %s : match  %s %s %s" % (physical_disk, left, operator, right))
                    match_count = match_count + 1
                    continue
                else:
                    debug("  %s : no match  %s %s %s" % (physical_disk, left, operator, right))
                    match_count = match_count
                    # nomatch

            # If all the features matched
            if match_count == len(current_lookup):
                info("  %50s matched" % (physical_disk))
                # When looking for an infinite number of disks, we can have
                # several disks per matching
                if disk not in matched_devices:
                    matched_devices[disk] = []
                matched_devices[disk].append(physical_disks[physical_disk])
                exclude_list.append(physical_disk)
                # If we look for an inifinite list of those devices, let's
                # continue looking for the same description unless let's go to
                # the next device
                if infinite is False:
                    break
            # We were unable to find all part of the required features
            elif match_count > 0:
                info("  %50s partially matched with %d/%d items" % (physical_disk, match_count, len(current_lookup)))
            else:
                info("  %50s no devices matched" % (physical_disk))

    final_list = {}
    for matched_device in matched_devices.keys():
        for n in range(0, len(matched_devices[matched_device]), 1):
            name = matched_device
            if len(matched_devices[matched_device]) > 1:
                name = "%s_%03d" % (matched_device, n)
            final_list[name] = matched_devices[matched_device][n]

    return final_list


def expand_disks(lookup_disks):
    '''
    Read the disks structure and expand them according to the count directive
    '''
    final_list = {}
    for disk in lookup_disks:
        infinite = False
        count = 0
        if 'count' not in lookup_disks[disk]:
            fatal("disk '%s' should have a 'count' value defined" % disk)
        if 'count' in lookup_disks[disk]:
            count = lookup_disks[disk]['count']
            del lookup_disks[disk]['count']

        if '*' in str(count).strip():
            infinite = True
            count = 1

        for n in range(0, int(count), 1):
            final_list["%s_%03d" % (disk, n)] = lookup_disks[disk]
            if infinite is True:
                final_list["%s_%03d" % (disk, n)]["infinite"] = "1"

    return final_list


def is_ceph_disk(partition):
    '''
    Check if a parition is used by ceph
    '''
    try:
        stdout = subprocess.check_output(["lsblk", "-no", "PARTLABEL", "%s" % partition])
        if "ceph data" in stdout:
            return True
    except:
        pass

    return False


def select_only_free_devices(physical_disks):
    ''' Don't keep that have partitions '''
    selected_devices = {}
    info('Detecting free devices')
    for physical_disk in sorted(physical_disks):
        ceph_disk = False
        current_physical_disk = physical_disks[physical_disk]

        # Don't consider devices that doesn't have partitions
        if 'partitions' not in current_physical_disk:
            info(' Ignoring %10s : Device doesnt support partitioning' % physical_disk)
            continue
        # Don't consider the device if partition list is not empty,
        if len(current_physical_disk['partitions']) > 0:
            for partition in current_physical_disk['partitions']:
                if is_ceph_disk("/dev/" + partition):
                    ceph_disk = True

            if ceph_disk is False:
                info(' Ignoring %10s : Device have exisiting partitions' % physical_disk)
                continue

        selected_devices[physical_disk] = physical_disks[physical_disk]
        selected_devices[physical_disk]['bdev'] = '/dev/' + physical_disk

        if ceph_disk is True:
            selected_devices[physical_disk]['ceph'] = 1
            info(' Adding   %10s : Ceph disk detected' % physical_disk)
        else:
            info(' Adding   %10s : %s' % (physical_disk, selected_devices[physical_disk]['bdev']))

    return selected_devices


def get_block_devices_persistent_name(physical_disks):
    ''' Replace the short name (sda) by the persistent naming 'by-id' '''
    directory = "/dev/disk/by-id/"

    info('Finding persistent disks name')
    # If the directory doesn't exist, reports the list as-is
    if not os.path.isdir(directory):
        info(' Cannot open %s' % directory)
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

    for physical_disk in sorted(physical_disks):
        if physical_disk in matching_list:
            current_index = sorted(matching_list[physical_disk])[0]
            final_list[current_index] = physical_disks[physical_disk]
            final_list[current_index]["bdev"] = "%s%s" % (directory, current_index)
            info(' Renaming %10s to %50s' % (physical_disk, current_index))
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


def show_resulting_devices(matched_devices, physical_disks):
    bdev_matched = []
    bdev_unmatched = []
    info("Matched devices   : %3d" % len(matched_devices))
    for matched_device in sorted(matched_devices.keys()):
        extra_string = ""
        if "ceph" in matched_devices[matched_device]:
            extra_string = " (ceph)"
        info(" %s : %s%s" % (matched_device, matched_devices[matched_device]["bdev"], extra_string))
        bdev_matched.append(matched_devices[matched_device]["bdev"])

    for physical_disk in sorted(physical_disks):
        if physical_disks[physical_disk]["bdev"] not in bdev_matched:
            bdev_unmatched.append(physical_disks[physical_disk]["bdev"])

    info("Unmatched devices : %3d" % len(bdev_unmatched))
    for bdev in sorted(bdev_unmatched):
        info(" %s" % bdev)


def info(message):
    global logger
    if logger:
        logger.info(message)


def warn(message):
    global logger
    if logger:
        logger.warn(message)


def debug(message):
    global logger
    if logger:
        logger.debug(message)


def error(message):
    global logger
    if logger:
        logger.error(message)


def setup_logging():
    global logger
    hdlr = logging.FileHandler('/var/log/choose_disk.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    logger.info("############")
    logger.info("# Starting #")
    logger.info("############")


def fatal(message):
    global module
    error(message)
    logger.info("#######")
    logger.info("# End #")
    logger.info("#######")
    if module:
        module.fail_json(msg=message)


def main():
    global module
    matched_devices = None
    lookup_disks = None
    disks = "disks"
    legacy = "legacy_disks"

    setup_logging()

    fields = {
        "facts": {"required": True, "type": "dict"},
        disks: {"required": False, "type": "dict"},
        legacy: {"required": False, "type": "str"},
    }

    module = AnsibleModule(
        argument_spec=fields,
        supports_check_mode=True
    )

    physical_disks = select_only_free_devices(module.params["facts"])

    if module.params[disks] and module.params[legacy]:
        fatal("%s and %s options are exclusive while both are defined" % (disks, legacy))

    # The new disks description is preferred over the legacy (/dev/sd) naming
    if module.params[disks]:
        info("Native syntax")
        info(" %s : %s" % (disks, module.params[disks]))
        # From the ansible facts, we only keep the disks that doesn't have
        # partitions, transform their device name in a persistent name
        lookup_disks = expand_disks(module.params[disks])
        physical_disks = get_block_devices_persistent_name(physical_disks)
    elif module.params[legacy]:
        info("Legacy syntax")
        info(" %s : %s" % (legacy, module.params[legacy]))
        # From the ansible facts, we only keep the disks that doesn't have partitions
        # We don't transform into the persistent naming but rather fake the disk
        # definition by creating "bdev" entries to get a feature to match.
        lookup_disks = expand_disks(fake_device(module.params[legacy]))
    else:
        fatal("no 'disks' or 'legacy_disks' variables found in playbook")
        return

    debug("Looking for %s" % lookup_disks)
    # From the ansible facts, we only keep the disks that doesn't have
    matched_devices = find_match(physical_disks, lookup_disks)

    show_resulting_devices(matched_devices, physical_disks)

    if len(matched_devices) < len(lookup_disks):
        fatal("Could only find %d of the %d expected devices\n" % (len(matched_devices), len(lookup_disks)))

    ceph_count = 0
    for matched_device in matched_devices:
        if "ceph" in matched_devices[matched_device]:
            ceph_count = ceph_count + 1

    changed = True
    logger.info("%d/%d disks already configured" % (ceph_count, len(matched_devices)))
    if ceph_count == matched_devices:
        changed = False

    message = "All searched devices were found"
    info(message)
    logger.info("#######")
    logger.info("# End #")
    logger.info("#######")
    module.exit_json(msg=message, changed=changed, ansible_facts=dict(devices=matched_devices))

if __name__ == '__main__':
        main()
