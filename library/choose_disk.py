#!/usr/bin/python
# Copyright 2017, Red Hat, Inc.
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
import logging
import os
import re
import subprocess

DOCUMENTATION = '''
module: choose_disk
author: Erwan Velu <erwan@redhat.com>
short_description: Choose disks based on their features
description:
    Ceph-ansible should pass the block devices to ceph-disk.
    But what disks to consider ?
    Passing block devices by their short path (/dev/sdx) means inconsistency
    across reboots or nodes.
    Using ids (/dev/disk/by-id) is too precise as it usually embedded a
    serial number.
    The solution is using a descriptive language to define "what" we are looking
    for : then this module search for the give disks and reports their id path.
    The module works in :
    - legacy mode where the module only make a few checks but doesn't search/rename the block devices. # noqa E501
    - native mode where user specify what disk to search base on its features
'''

# The following set of functions are used to compare units
# To insure we compare similar metrics, we convert them with to_bytes()
# into the same unit (i.e to avoid comparing GB and MB)


def _equal(left, right):
    '''
    Function to test equality when comparing features
    '''
    return to_bytes(left) == to_bytes(right)


def _gt(left, right):
    '''
    Function to test superiority (greater than) when comparing features
    '''
    return float(to_bytes(left)) > float(to_bytes(right))


def _gte(left, right):
    '''
    Function to test superiority (greater than or equal) when comparing features
    '''
    return float(to_bytes(left)) >= float(to_bytes(right))


def _lt(left, right):
    '''
    Function to test inferiority (greater than) when comparing features
    '''
    return float(to_bytes(left)) < float(to_bytes(right))


def _lte(left, right):
    '''
    Function to test inferiority (greater than or equal) when comparing features
    '''
    return float(to_bytes(left)) <= float(to_bytes(right))


def _and(left, right):
    '''
    Function to test "left and right"
    '''
    return left and right


def get_alias(operator, left, right):
    '''
    Function to translate some virtual operators into real ones
    '''
    aliases = {
        "between": "and(gt(%s),lt(%s))" % (left, right),
        "between_e": "and(gte(%s),lte(%s))" % (left, right)
    }
    for alias in aliases:
        if alias in operator:
            return aliases[alias]


_REGEXP = re.compile(r'^([^(]+)'          # function name
                     r'\(\s*([^,]+)'      # first argument
                     r'(?:\s*,\s*(.+))?'  # remaining optional arguments
                     r'\)$')              # last parenthesis


logger = logging.getLogger('choose_disk')


def to_bytes(value):
    '''
    Convert storage units into bytes to ease comparaison between different units
    '''
    value = str(value).lower().strip()

    storage_units = {'kb': 1024,
                     'kib': 1000,
                     'mb': 1024 * 1024,
                     'mib': 1000 * 1000,
                     'gb': 1024 * 1024 * 1024,
                     'gib': 1000 * 1000 * 1000,
                     'tb': 1024 * 1024 * 1024 * 1024,
                     'tib': 1000 * 1000 * 1000 * 1000,
                     'pb': 1024 * 1024 * 1024 * 1024 * 1024,
                     'pib': 1000 * 1000 * 1000 * 1000 * 1000}

    # Units are storage units
    for size in storage_units.keys():
        if size in value:
            real_value = value.replace(size, "")
            return str(float(real_value) * storage_units[size])

    return value


def get_keys_by_ceph_order(physical_disks, expected_type):
    '''
    Return a list of keys where ceph disks are reported first
    while keeping the list sorted.
    We need to return ceph disks first to insure they are reused in priority.
    '''
    ceph_disks = []
    non_ceph_disks = []

    for physical_disk in sorted(physical_disks):
        if "ceph_prepared" in physical_disks[physical_disk]:
            # We shall only return the ceph disks from the same type
            # If we search for journals, don't return data disks :
            #   Note that we don't neither them into 'non_ceph_disks' as they are not free
            pdisk = dict(physical_disks[physical_disk])

            if expected_type in pdisk["ceph_prepared"]:
                logger.debug("get_keys_by_ceph_order: Keeping %s", physical_disk)
                ceph_disks.append(physical_disk)
            else:
                logger.debug("get_keys_by_ceph_order: %s doesn't have the proper ceph type", physical_disk)  # noqa E501
        else:
            non_ceph_disks.append(physical_disk)

    return ceph_disks + non_ceph_disks


def evaluate_operator(left, right, module=None):
    '''
    Evaluate lines splitted in left/right items
    '''

    # associate a keyword and the associated function
    OPERATORS = {
        "=": _equal,
        "equal": _equal,
        "gt": _gt,
        "gte": _gte,
        "lt": _lt,
        "lte": _lte,
        "and": _and,
    }

    # Default comparing operator is equal
    operator = "equal"

    # Test if we have another operator in the right operand
    arguments = _REGEXP.search(right)
    if arguments:
            new_operator = arguments.group(1)

            # Some operators are aliases to more complex commands.
            # Let's make the substition in place and restart with it
            alias = get_alias(new_operator, arguments.group(2), arguments.group(3))
            if alias:
                return evaluate_operator(left, alias, module)

            # Check if the associated function exists
            if new_operator in OPERATORS:
                # and assign operands with the new values
                operator = new_operator
                right = arguments.group(2)
                new_arguments = _REGEXP.search(right)
                if new_arguments:
                    # Don't forget to evaluate the two sides of the expression
                    # Typical case when we shall compare a 'value' with : 'and( gt(x), lt(y) )'
                    # The looking value always stays to the 'left' part of the expression
                    new_right = arguments.group(3)
                    return OPERATORS[operator](evaluate_operator(left, right, module), evaluate_operator(left, new_right, module))  # noqa E501
                    #           and           (                  value,gt(x)        ),                  (value,lt(y)            ) # noqa E501
            else:
                fatal("Unsupported '%s' operator in: %s" % (new_operator, right), module)
    return OPERATORS[operator](left, right)


def find_match(physical_disks, lookup_disks, module=None):
    '''
    Find a set of matching devices in physical_disks
    '''
    matched_devices = {}
    ignored_devices = []

    logger.info("Looking for matches")

    # Inspecting every disk we search for
    for disk in sorted(lookup_disks):

        infinite = False
        current_lookup = dict(lookup_disks[disk])
        current_type = ""

        # Does the user want _all_ the devices matching that description ?
        if "infinite" in current_lookup:
            infinite = True
            del current_lookup["infinite"]

        # We cannot keep the disk type as a feature to lookup unless the
        # matching with a real device would fail
        current_type = current_lookup["ceph_type"]
        del current_lookup["ceph_type"]

        if len(ignored_devices) == len(physical_disks):
            logger.info("Skipping %s as no more free devices to match", disk)
            continue

        logger.info("Inspecting %s", disk)
        # Trying to find a match against all physical disks we have
        for physical_disk in get_keys_by_ceph_order(physical_disks, current_type):
            # Avoid reusing an already matched physical disk
            if physical_disk in ignored_devices:
                continue

            current_physical_disk = physical_disks[physical_disk]
            match_count = 0
            # Checking what features are matching
            for feature in current_lookup:
                if feature not in current_physical_disk:
                    continue

                # Assign left and right operands
                right = current_lookup[feature]
                left = current_physical_disk[feature]

                # Let's check if (left <operator> right) is True meaning the match is done
                if evaluate_operator(left, right, module):
                    logger.debug(" %s : match %s %s", physical_disk, left, right)
                    match_count = match_count + 1
                    continue
                else:
                    # comparaison is false meaning devices doesn't match
                    logger.debug(" %s : no match %s %s", physical_disk, left, right)

            # If all the features matched
            if match_count == len(current_lookup):
                logger.info(" %50s matched", physical_disk)

                # When looking for an infinite number of disks,
                # we can have several disks per matching
                if disk not in matched_devices:
                    matched_devices[disk] = []

                # Reintroducing the disk type to keep disks categories alive
                pdisk = dict(physical_disks[physical_disk])
                pdisk["ceph_type"] = current_type

                # The matching disk is saved and
                # reported as one to be ignored for the next iterations
                matched_devices[disk].append(pdisk)
                ignored_devices.append(physical_disk)

                # If we look for an inifinite list of those devices, let's
                # continue looking for the same description unless let's go to
                # the next device
                if infinite is False:
                    break
            elif match_count > 0:
                # We only found a subset of the required features
                logger.info(" %50s partially matched with %d/%d items",
                            physical_disk, match_count, len(current_lookup))
            else:
                logger.info(" %50s no devices matched", physical_disk)

    # Let's prepare the final output
    final_disks = {}

    # Matching devices are named base on the user-provided name + incremental number
    # If we look for {'storage_disks': {'count': 2, 'ceph_type': 'data', 'vendor': '0x1af4', 'size': 'gte(20 GB)'}} # noqa E501
    # - first device will be named  : storage_disks_000
    # - second device will be named : storage_disks_001
    for matched_device in matched_devices:
        for n in range(0, len(matched_devices[matched_device])):
            name = matched_device
            if len(matched_devices[matched_device]) > 1:
                name = "%s_%03d" % (matched_device, n)
            final_disks[name] = matched_devices[matched_device][n]

    return final_disks


def expand_disks(lookup_disks, ceph_type="", module=None):
    '''
    Read the disks structure and expand them according to the count directive
    '''
    final_disks = {}

    for disk in lookup_disks:
        infinite = False
        count = 0
        if ceph_type:
            # When legacy is enabled, let's enforce the count & type
            count = 1
            lookup_disks[disk]['ceph_type'] = ceph_type
        else:
            if 'count' not in lookup_disks[disk]:
                fatal("disk '%s' should have a 'count' value defined" % disk, module)
            if 'ceph_type' not in lookup_disks[disk]:
                fatal("disk '%s' should have a 'ceph_type' value defined : {data | journal}" % disk, module)  # noqa E501
            if lookup_disks[disk]['ceph_type'] not in ['data', 'journal']:
                fatal("disk '%s' doesn't have a valid 'ceph_type' defined, it should be : {data | journal}" % disk, module)   # noqa E501
            if 'count' in lookup_disks[disk]:
                count = lookup_disks[disk]['count']
                del lookup_disks[disk]['count']

        #  If the count field is set to '*', let's consider an infinite number of devices to match
        if '*' in str(count).strip():
            infinite = True
            count = 1

        for n in range(0, int(count), 1):
            final_disks["%s_%03d" % (disk, n)] = lookup_disks[disk]
            if infinite is True:
                final_disks["%s_%03d" % (disk, n)]["infinite"] = "1"

    return final_disks


def disk_label(partition):
    '''
    Reports if a partition is containing some ceph structures
    '''
    import json
    # First, let's search for legacy
    stdout = subprocess.check_output(["lsblk", "-no", "PARTLABEL", "%s" % partition])

    if "ceph data" in stdout:
        return "data"

    if "ceph journal" in stdout:
        return "journal"

    # Then, let's search for metadata coming from ceph-volume
    output_cmd = subprocess.Popen("ceph-volume lvm list --format=json {}".format(partition),
                                  shell=True, stdout=subprocess.PIPE)
    raw_json, _ = output_cmd.communicate()
    json = json.loads(raw_json)
    for item in json:
        current_item = json[item]
        if "type" in current_item[0]:
            return current_item[0]["type"]
        else:
            return "undefined"
    return ""


def select_only_free_devices(physical_disks):
    '''
    It's important reporting only devices that are not currently used.
    '''
    selected_devices = {}
    logger.info('Detecting free devices')

    for physical_disk in sorted(physical_disks):
        ceph_disk = ""
        current_physical_disk = physical_disks[physical_disk]

        # Don't consider devices that doesn't support partitions
        if 'partitions' not in current_physical_disk:
            logger.info('Ignoring %10s : device does not support partitioning', physical_disk)
            continue

        # Removing Cdrom Devices
        if physical_disk.startswith("sr") or physical_disk.startswith("cdrom"):
            logger.info('Ignoring %10s : cdrom device', physical_disk)
            continue

        # Removing Read-only devices
        stdout = subprocess.check_output(["blockdev", "--getro", "/dev/%s" % physical_disk])
        if "1" in stdout:
            logger.info('Ignoring %10s : read-only device', physical_disk)
            continue

        # Does the disk belongs to a LVM ?
        return_code = os.system("pvdisplay -c /dev/{}".format(physical_disk))
        if return_code == 0:
            logger.info('Ignoring %10s : device is already used by LVM', physical_disk)
            continue

        # Don't consider the device if partition list is not empty,
        # A disk that is already partionned may contain important data
        # It's up to the admin to zap the device before using it in ceph-ansible
        # There is only an exception :
        #    if the partitions are from ceph, it surely means that we have to
        #    reuse them
        if len(current_physical_disk['partitions']) > 0:
            for partition in sorted(current_physical_disk['partitions']):
                disk_type = disk_label("/dev/" + partition)
                if disk_type and disk_type not in ceph_disk:
                    if ceph_disk:
                        ceph_disk += " + "
                    # Saving the ceph type (journal and/or data)
                    ceph_disk += disk_type

            if not ceph_disk:
                logger.info('Ignoring %10s : device has existing partitions', physical_disk)
                continue

        selected_devices[physical_disk] = physical_disks[physical_disk]
        selected_devices[physical_disk]['bdev'] = '/dev/' + physical_disk

        if ceph_disk:
            selected_devices[physical_disk]['ceph_prepared'] = ceph_disk
            logger.info('Adding   %10s : Ceph disk detected (%s)', physical_disk, ceph_disk)
        else:
            logger.info('Adding   %10s : %s', physical_disk, selected_devices[physical_disk]['bdev'])  # noqa E501

    return selected_devices


def get_block_devices_persistent_name(physical_disks):
    '''
    Replace the short name (sda) by the persistent naming 'by-id'
    '''
    directory = "/dev/disk/by-id/"

    logger.info('Finding persistent disks name')

    # If the directory doesn't exist, reports the list as-is
    if not os.path.isdir(directory):
        logger.info('Cannot open %s', directory)
        return physical_disks

    final_disks = {}
    matching_devices = {}

    # Searching in the /dev/disk/by-id/ which are the disks we look for
    for root, dirs, files in os.walk(directory, topdown=False):
        for f in files:
            device_name = os.path.basename(os.readlink(os.path.join(root, f)))
            if device_name in physical_disks:
                if device_name not in matching_devices:
                    matching_devices[device_name] = [f]
                else:
                    matching_devices[device_name].append(f)

    # Saving matching disks and add the path of the block device
    # Output is like : Renaming        vdb to                        virtio-e0b94c7d-75ca-4175-a
    for physical_disk in sorted(physical_disks):
        if physical_disk in matching_devices:
            current_index = sorted(matching_devices[physical_disk])[0]
            final_disks[current_index] = physical_disks[physical_disk]
            final_disks[current_index]["bdev"] = "%s%s" % (directory, current_index)
            logger.info('Renaming %10s to %50s', physical_disk, current_index)
        else:
            current_index = physical_disk
            final_disks[current_index] = physical_disks[physical_disk]

    return final_disks


def fake_device(legacy_devices, ceph_type):
    '''
    In case of legacy block device names, let's create an internal faked
    entry with a 'bdev' entry filled with the actual path. This will be used to
    make a match later on.
    '''
    devices = {}
    count = 0
    for device in legacy_devices:
        devices["%s_%d" % (ceph_type, count)] = {"bdev": os.path.join(os.path.dirname(device),
                                                                      os.path.basename(device))}
        count = count + 1

    return devices


def show_resulting_devices(matched_devices, physical_disks):
    '''
    Print the current state :
      - what devices matched
      - what devices didn't matched
    '''
    bdev_matched = []
    bdev_unmatched = []

    def prepare_device_string(device):
        device_string = ""
        if "ceph_prepared" in device:
            device_string += " (ceph %s)" % device["ceph_prepared"]
        device_string += " : "
        for feature in ["vendor", "model", "size", "rotational"]:
            if feature in device:
                device_string += "%s:%s " % (feature[0], device[feature])

        return device_string

    logger.info("Matched devices   : %3d", len(matched_devices))
    for matched_device in sorted(matched_devices):
        logger.info(" %s : %s%s",
                    matched_device,
                    matched_devices[matched_device]["bdev"],
                    prepare_device_string(matched_devices[matched_device]))
        bdev_matched.append(matched_devices[matched_device]["bdev"])

    for physical_disk in sorted(physical_disks):
        pdisk = physical_disks[physical_disk]
        if pdisk["bdev"] not in bdev_matched:
            bdev_unmatched.append("%s %s" % (pdisk["bdev"], prepare_device_string(pdisk)))

    logger.info("Unmatched devices : %3d", len(bdev_unmatched))
    for bdev in sorted(bdev_unmatched):
        logger.info(" %s", bdev)


def setup_logging(filename=None):
    '''
    Preparing the logging system
    '''
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    if filename:
        hdlr = logging.FileHandler(filename)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    logger.info("############")
    logger.info("# Starting #")
    logger.info("############")


def fatal(message, module):
    '''
    Report a fatal error and exit
    '''
    logger.error("### FATAL ###")
    logger.error(message)
    logger.error("#############")
    logger.info("#######")
    logger.info("# End #")
    logger.info("#######")
    if module:
        module.fail_json(msg=message)
    else:
        exit(1)


def get_var(module, variable):
    '''
    Extract the ansible variable from the playbook
    If variable doesn't exist, let's return None
    '''
    if variable in module.params["vars"]:
        return module.params["vars"][variable]


def main():
    module = None
    legacy = False
    matched_devices = None
    lookup_disks = None

    setup_logging()

    fields = {
        "vars": {"required": True, "type": "dict"},
    }

    module = AnsibleModule(
        argument_spec=fields,
        supports_check_mode=True
    )

    # Loading variables from vars
    ansible_devices = get_var(module, "ansible_devices")
    if not ansible_devices:
        fatal("Missing ansible_devices in vars !", module)

    physical_disks = select_only_free_devices(ansible_devices)

    devices = get_var(module, "devices")

    # The new disks description is preferred over the legacy (/dev/sdx) naming
    if isinstance(devices, dict):
        logger.info("Native syntax")
        logger.info("devices : %s", devices)
        # From the ansible facts, we only keep disks that doesn't have
        # partitions, transform their device name in a persistent name
        lookup_disks = expand_disks(devices, "", module)
        physical_disks = get_block_devices_persistent_name(physical_disks)
    elif isinstance(devices, list):
        legacy = True
        logger.info("Legacy syntax")
        logger.info("devices : %s", devices)

        # In case of legacy, we search for a possible presence of raw_journal_devices
        raw_journal_devices = get_var(module, "raw_journal_devices")

        # From the ansible facts, we only keep the disks that doesn't have partitions
        # We don't transform into the persistent naming but rather fake the disk
        # definition by creating "bdev" entries to get a feature to match.
        lookup_disks = expand_disks(fake_device(devices, "data"), "data", module)
        if raw_journal_devices:
            logger.info("raw_journal_devices : %s", raw_journal_devices)
            lookup_disks.update(expand_disks(fake_device(raw_journal_devices, "journal"), "journal", module))  # noqa E501
    else:
        fatal("devices variable should be a dict for native syntax {...} or "
              "a list for legacy syntax [ ... ] : %s detected" % type(devices), module)

    # Final checks between the lookup & the actual ansible configuration
    for disk in lookup_disks:
        if get_var(module, "journal_collocation") is True:
            if lookup_disks[disk]["ceph_type"] == "journal":
                fatal("We cannot search for journal devices when 'journal_collocation' is set", module)  # noqa E501

    logger.debug("Looking for %s", lookup_disks)

    matched_devices = find_match(physical_disks, lookup_disks, module)

    show_resulting_devices(matched_devices, physical_disks)

    if len(matched_devices) < len(lookup_disks):
        fatal("Could only find %d of the %d expected devices" % (len(matched_devices),
                                                                 len(lookup_disks)), module)

    # Preparing the final output by deivces in several categories
    # - data disks for ceph
    # - disks to enable in ceph
    # - journals
    ceph_data = []
    journal = []
    to_activate = []
    ceph_count = 0
    for matched_device in matched_devices:
        device = matched_devices[matched_device]
        device['name'] = matched_device
        if "ceph_prepared" in device:
            if "data" in device["ceph_prepared"]:
                ceph_count = ceph_count + 1
                to_activate.append(device["bdev"])
            continue
        if "data" in device["ceph_type"]:
                ceph_data.append(device["bdev"])
                continue
        if "journal" in device["ceph_type"]:
            journal.append(device["bdev"])

    changed = True
    logger.info("%d/%d disks already configured", ceph_count, len(matched_devices))
    # If we only report already ceph-prepared disks, let's report nothing
    # changed to Ansible
    if ceph_count == len(matched_devices):
        changed = False

    message = "All searched devices were found"
    logger.info(message)
    logger.info("#######")
    logger.info("# End #")
    logger.info("#######")

    if legacy is True:
        # Reporting devices & raw_journal_devices for compatiblity
        module.exit_json(msg=message, changed=changed,
                         ansible_facts=dict(legacy_devices=ceph_data,
                                            journal_devices=journal,
                                            devices_to_activate=to_activate,
                                            storage_devices=[]))
    else:
        # Reporting storage_devices & journal_devices
        module.exit_json(msg=message, changed=changed,
                         ansible_facts=dict(storage_devices=ceph_data,
                                            journal_devices=journal,
                                            devices_to_activate=to_activate,
                                            legacy_devices=[]))


if __name__ == '__main__':
        main()
