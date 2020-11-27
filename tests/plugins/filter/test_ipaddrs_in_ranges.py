from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleFilterError

import ipaddrs_in_ranges
import pytest

pytest.importorskip('netaddr')

filter_plugin = ipaddrs_in_ranges.FilterModule()


class TestIpaddrsInRanges(object):

    def test_one_ip_one_range(self):
        ips = ['10.10.10.1']
        ranges = ['10.10.10.1/24']
        result = filter_plugin.ips_in_ranges(ips, ranges)
        assert ips[0] in result
        assert len(result) == 1

    def test_two_ip_one_range(self):
        ips = ['192.168.1.1', '10.10.10.1']
        ranges = ['10.10.10.1/24']
        result = filter_plugin.ips_in_ranges(ips, ranges)
        assert ips[0] not in result
        assert ips[1] in result
        assert len(result) == 1

    def test_one_ip_two_ranges(self):
        ips = ['10.10.10.1']
        ranges = ['192.168.1.0/24', '10.10.10.1/24']
        result = filter_plugin.ips_in_ranges(ips, ranges)
        assert ips[0] in result
        assert len(result) == 1

    def test_multiple_ips_multiple_ranges(self):
        ips = ['10.10.10.1', '192.168.1.1', '172.16.10.1']
        ranges = ['192.168.1.0/24', '10.10.10.1/24', '172.16.17.0/24']
        result = filter_plugin.ips_in_ranges(ips, ranges)
        assert ips[0] in result
        assert ips[1] in result
        assert ips[2] not in result
        assert len(result) == 2

    def test_no_ips_in_ranges(self):
        ips = ['10.10.20.1', '192.168.2.1', '172.16.10.1']
        ranges = ['192.168.1.0/24', '10.10.10.1/24', '172.16.17.0/24']
        result = filter_plugin.ips_in_ranges(ips, ranges)
        assert len(result) == 0

    def test_ips_in_ranges_in_filters_dict(self):
        assert 'ips_in_ranges' in filter_plugin.filters()

    def test_missing_netaddr_module(self):
        ipaddrs_in_ranges.netaddr = None

        with pytest.raises(AnsibleFilterError) as result:
            filter_plugin.filters()

        assert result.type == AnsibleFilterError
        assert str(result.value) == "The ips_in_ranges filter requires python's netaddr be installed on the ansible controller."
