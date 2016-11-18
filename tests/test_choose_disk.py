import imp
import inspect
import library.choose_disk as choose_disk
import mock
import os
from nose.tools import assert_equals, nottest

host_dir = "tests/unit/hosts/"


@nottest
def get_hosts_to_test():
    # Retrieve what function called us
    caller = inspect.stack()[1][3]

    hosts = []
    # List all the possible modules
    for host in os.listdir(host_dir):
        if host.endswith(".py"):
            # Load the module
            host_file = imp.load_source(host, host_dir + host)
            # If the module have the associated pepare_ function, return it
            if (hasattr(host_file, "prepare_" + caller)):
                hosts.append(host_file)
    return hosts


def test_expand_disks_explict_count_1():
    """
    expand_disks - test expand disk with explicit count=1
    """
    result = choose_disk.expand_disks(eval("{'storage_disks': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1', 'count': 1 }}"))
    assert_equals(result, eval("{'storage_disks_0': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1'}}"))


def test_expand_disks_explict_count_2():
    """
    expand_disks - test expand disk with explicit count=2
    """
    result = choose_disk.expand_disks(eval("{'storage_disks': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1', 'count': 2 }}"))
    assert_equals(result, eval("{'storage_disks_0': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1'}, 'storage_disks_1': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1'}}"))


def test_expand_disks_implicit_count():
    """
    expand_disks - test expand disk with implicit count=1
    """
    result = choose_disk.expand_disks(eval("{'storage_disks': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1'}}"))
    assert_equals(result, eval("{'storage_disks_0': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1'}}"))


def test_expand_disks_multiple_implicit_count():
    """
    expand_disks - test expand disk with two implicit count=1
    """
    result = choose_disk.expand_disks(eval("{'storage_disks': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1'},\
                                             'journal_disks': {'model': 'SANDISK PLIPM512', 'rotational': '0'}}"))
    assert_equals(result, eval("{'journal_disks_0': {'model': 'SANDISK PLIPM512', 'rotational': '0'},\
                                 'storage_disks_0': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1'}}"))


def test_units_gb():
    """
    convert_units - checking storage units are well converted in bytes
    """
    units = {'100 MB': '104857600.0', '1 GIB': '1000000000.0', ' 1 Kb ': '1024.0'}

    for unit in units.keys():
        assert_equals(choose_disk.convert_units(unit), units[unit])


def test_find_match_matched():
    """
    find_match - test for a matching device
    """
    for host_file in get_hosts_to_test():
        disk_0, expected_result = host_file.prepare_test_find_match_matched()
        result = choose_disk.find_match(host_file.ansible_devices, disk_0)
        assert_equals(result, expected_result)


def test_find_match_matched_gt():
    """
    find_match - test for a matching device with gt() operator
    """
    ansible_devices = {'sr0': {'sectorsize': '512'}}
    disk_0 = {'storage_disks_0': {'sectorsize': 'gt(256)'}}
    expected_result = ansible_devices
    result = choose_disk.find_match(ansible_devices, disk_0)
    assert_equals(result, expected_result)


def test_find_match_matched_lt():
    """
    find_match - test for a matching device with lt() operator
    """
    ansible_devices = {'sr0': {'sectorsize': '512'}}
    disk_0 = {'storage_disks_0': {'sectorsize': 'lt(1024)'}}
    expected_result = ansible_devices
    result = choose_disk.find_match(ansible_devices, disk_0)
    assert_equals(result, expected_result)


def test_find_match_matched_gt_units():
    """
    find_match - test for a matching device with gt() operator and units
    """
    ansible_devices = {'sr0': {'size': '200.00 MB'}}
    disk_0 = {'storage_disks_0': {'size': 'gt(100.00 MB)'}}
    expected_result = ansible_devices
    result = choose_disk.find_match(ansible_devices, disk_0)
    assert_equals(result, expected_result)

    disk_0 = {'storage_disks_0': {'size': 'lt(1 GB)'}}
    expected_result = ansible_devices
    result = choose_disk.find_match(ansible_devices, disk_0)
    assert_equals(result, expected_result)


def test_find_match_unmatched():
    """
    find_match - test for a non-matching device
    """
    for host_file in get_hosts_to_test():
        disk_0, expected_result = host_file.prepare_test_find_match_unmatched()
        result = choose_disk.find_match(host_file.ansible_devices, disk_0)
        assert_equals(result, expected_result)


def test_select_only_free_devices():
    """
    select_only_free_devices - Removing devices that have partitions
    """

    for host_file in get_hosts_to_test():
        expected_result = host_file.prepare_test_select_only_free_devices()
        result = choose_disk.select_only_free_devices(host_file.ansible_devices)
        assert_equals(result, expected_result)


def test_get_block_devices_persistent_name():
    """
    get_block_devices_persistent_name - Looking persistent name for listed block devices
    """
    for host_file in get_hosts_to_test():
        disk_facts, expected_result = host_file.prepare_test_get_block_devices_persistent_name()

        def fake_readlink(name):
            return host_file.disk_by_id[name.split('/')[-1]]

        with mock.patch('library.choose_disk.os') as mocked_os:
            mocked_os.readlink.side_effect = fake_readlink
            mocked_os.listdir.return_value = host_file.disk_by_id.keys()
            result = choose_disk.get_block_devices_persistent_name(disk_facts)
            assert_equals(result, expected_result)

# test_choosedisk.py ends here
