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

import imp
import inspect
import mock
import os
from . import choose_disk

host_dir = "library/unit/hosts/"


def get_hosts_to_test():
    # Retrieve what function called us
    caller = inspect.stack()[1][3]

    hosts = []
    # List all the possible modules
    for host in os.listdir(host_dir):
        if host.endswith(".py"):
            # Load the module
            host_file = imp.load_source(host, host_dir + host)
            # If the module has the associated pepare_ function, return it
            if (hasattr(host_file, "prepare_" + caller)):
                hosts.append(host_file)
    return hosts


def test_expand_disks_explicit_count_1():
    """
    expand_disks - test expand disk with explicit count=1
    """
    result = choose_disk.expand_disks(
        {'storage_disks': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1', 'count': 1, 'ceph_type': 'data'}})  # noqa E501
    assert result == {'storage_disks_000': {
        'model': 'SAMSUNG MZ7LN512', 'rotational': '1', 'ceph_type': 'data'}}


def test_expand_disks_explicit_count_2():
    """
    expand_disks - test expand disk with explicit count=2
    """
    result = choose_disk.expand_disks(
        {'storage_disks': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1', 'count': 2, 'ceph_type': 'data'}})  # noqa E501
    assert result == {'storage_disks_000': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1', 'ceph_type': 'data'},  # noqa E501
                      'storage_disks_001': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1', 'ceph_type': 'data'}}  # noqa E501


def test_fake_device():
    """
    fake_device - Testing the legacy conversion of disk's definition
    """
    fake_device = choose_disk.fake_device(["/dev/sda", "/dev/sdb", "/dev/sdc"], "data")
    result = {'data_0': {'bdev': '/dev/sda'},
              'data_1': {'bdev': '/dev/sdb'},
              'data_2': {'bdev': '/dev/sdc'}}

    assert fake_device == result


def test_expand_disks_legacy():
    """
    expand_disks - expanding legacy devices
    """
    result = choose_disk.expand_disks(choose_disk.fake_device(
        ["/dev/sda", "/dev/sdb", "/dev/sdc"], "data"), "data")
    assert result == {'data_1_000': {'ceph_type': 'data', 'bdev': '/dev/sdb'}, 'data_0_000': {
        'ceph_type': 'data', 'bdev': '/dev/sda'}, 'data_2_000': {'ceph_type': 'data', 'bdev': '/dev/sdc'}}  # noqa E501


def test_units_gb():
    """
    to_bytes - checking storage units are well converted in bytes
    """
    units = {'100 MB': 104857600.0, '1 GIB': 1000000000.0,
             ' 1 Kb ': 1024.0, ' 1giB ': 1000000000.0, '1': 1.0}

    for unit in units.keys():
        assert choose_disk.to_bytes(unit) == units[unit]


def test_find_match_matched():
    """
    find_match - test for a matching device
    """
    for host_file in get_hosts_to_test():
        disk_0, expected_result = host_file.prepare_test_find_match_matched()
        result = choose_disk.find_match(host_file.ansible_devices, disk_0)
        assert result == expected_result


def test_find_match_matched_gt():
    """
    find_match - test for a matching device with gt() operator
    """
    ansible_devices = {'sr0': {'sectorsize': '512', 'ceph_type': 'data'}}
    disk_0 = {'sr0': {'sectorsize': {'gt': 256}, 'ceph_type': 'data'}}
    expected_result = ansible_devices
    result = choose_disk.find_match(ansible_devices, disk_0)
    assert result == expected_result


def test_find_match_matched_lt():
    """
    find_match - test for a matching device with lt() operator
    """
    ansible_devices = {'sr0': {'sectorsize': '512', 'ceph_type': 'data'}}
    disk_0 = {'sr0': {'sectorsize': {'lt': 1024}, 'ceph_type': 'data'}}
    expected_result = ansible_devices
    result = choose_disk.find_match(ansible_devices, disk_0)
    assert result == expected_result


def test_find_match_matched_between():
    """
    find_match - test for a matching device with between() operator
    """
    ansible_devices = {'sr0': {'sectorsize': '512', 'ceph_type': 'data'}}
    disk_0 = {'sr0': {'sectorsize': {'and': [{'gt': 511}, {'lt': 513}]}, 'ceph_type': 'data'}}
    expected_result = ansible_devices
    choose_disk.setup_logging()
    result = choose_disk.find_match(ansible_devices, disk_0)
    assert result == expected_result


def test_find_match_matched_between_e():
    """
    find_match - test for a matching device with between_e() operator
    """
    ansible_devices = {'sr0': {'sectorsize': '512', 'ceph_type': 'data'}}
    disk_0 = {'sr0': {'sectorsize': {
        'and': [{'ge': 512}, {'le': 512}]}, 'ceph_type': 'data'}}
    expected_result = ansible_devices
    choose_disk.setup_logging()
    result = choose_disk.find_match(ansible_devices, disk_0)
    assert result == expected_result


def test_find_match_matched_gt_units():
    """
    find_match - test for a matching device with gt() operator and units
    """
    ansible_devices = {'sr0': {'size': '200.00 MB', 'ceph_type': 'data'}}
    disk_0 = {'sr0': {'size': {'gt': '100 MB'}, 'ceph_type': 'data'}}
    expected_result = ansible_devices
    result = choose_disk.find_match(ansible_devices, disk_0)
    assert result == expected_result

    disk_0 = {'sr0': {'size': {'lt': '1 GB'}, 'ceph_type': 'data'}}
    expected_result = ansible_devices
    result = choose_disk.find_match(ansible_devices, disk_0)
    assert result == expected_result


def test_find_match_unmatched():
    """
    find_match - test for a non-matching device
    """
    for host_file in get_hosts_to_test():
        disk_0, expected_result = host_file.prepare_test_find_match_unmatched()
        result = choose_disk.find_match(host_file.ansible_devices, disk_0)
        assert result == expected_result


def test_select_only_free_devices():
    """
    select_only_free_devices - Removing devices that have partitions
    """
    for host_file in get_hosts_to_test():
        with mock.patch('library.choose_disk.read_ceph_disk', host_file.read_ceph_disk):
            with mock.patch('library.choose_disk.is_read_only_device', host_file.is_read_only_device):  # noqa 501
                with mock.patch('library.choose_disk.get_ceph_volume_lvm_list', host_file.get_ceph_volume_lvm_list):  # noqa 501
                    with mock.patch('library.choose_disk.is_invalid_partition_table', host_file.is_invalid_partition_table):  # noqa 501
                        with mock.patch('library.choose_disk.get_partition_label', host_file.get_partition_label):  # noqa 501
                            with mock.patch('library.choose_disk.is_lvm_disk', host_file.is_lvm_disk):  # noqa 501
                                with mock.patch('library.choose_disk.is_locked_raw_device', host_file.is_locked_raw_device):  # noqa 501
                                    expected_result = host_file.prepare_test_select_only_free_devices()  # noqa 501
                                    result = choose_disk.select_only_free_devices(host_file.ansible_devices, host_file.fake_fsid)  # noqa 501
        assert result == expected_result


# test_choosedisk.py ends here
