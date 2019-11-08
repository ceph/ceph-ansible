from ansible import errors

try:
    import netaddr
except ImportError:
    # in this case, we'll make the filter return an error message (see bottom)
    netaddr = None


class FilterModule(object):
    ''' IP addresses within IP ranges '''

    def ips_in_ranges(self, ip_addresses, ip_ranges):
        ips_in_ranges = list()
        for ip_addr in ip_addresses:
            for ip_range in ip_ranges:
                if netaddr.IPAddress(ip_addr) in netaddr.IPNetwork(ip_range):
                    ips_in_ranges.append(ip_addr)
        return ips_in_ranges

    def filters(self):
        if netaddr:
            return {
                'ips_in_ranges': self.ips_in_ranges
            }
        else:
            # Need to install python's netaddr for these filters to work
            raise errors.AnsibleFilterError(
                "The ips_in_ranges filter requires python's netaddr be "
                "installed on the ansible controller.")
