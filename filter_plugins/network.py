import ipcalc


# Old versions don't have this method.
if not hasattr(ipcalc.IP, 'to_compressed'):
    import re

    # Shamelessly copied from
    # https://github.com/tehmaze/ipcalc/blob/master/ipcalc.py
    def to_compressed(address):
        '''
        Compress an IP address to its shortest possible compressed form.

        >>> print IP('127.0.0.1').to_compressed()
        127.1
        >>> print IP('127.1.0.1').to_compressed()
        127.1.1
        >>> print IP('127.0.1.1').to_compressed()
        127.0.1.1
        >>> print IP('2001:1234:0000:0000:0000:0000:0000:5678').to_compressed()
        2001:1234::5678
        >>> print IP('1234:0000:0000:beef:0000:0000:0000:5678').to_compressed()
        1234:0:0:beef::5678
        >>> print IP('0000:0000:0000:0000:0000:0000:0000:0001').to_compressed()
        ::1
        >>> print IP('fe80:0000:0000:0000:0000:0000:0000:0000').to_compressed()
        fe80::
        '''

        if address.v == 4:
            quads = address.dq.split('.')
            try:
                zero = quads.index('0')
                if zero == 1 and quads.index('0', zero + 1):
                    quads.pop(zero)
                    quads.pop(zero)
                    return '.'.join(quads)
                elif zero == 2:
                    quads.pop(zero)
                    return '.'.join(quads)
            except ValueError:  # No zeroes
                pass

            return address.dq
        else:
            quads = map(lambda q: '%x' % (int(q, 16)), address.dq.split(':'))
            quadc = ':%s:' % (':'.join(quads),)
            zeros = [0, -1]

            # Find the largest group of zeros
            for match in re.finditer(r'(:[:0]+)', quadc):
                count = len(match.group(1)) - 1
                if count > zeros[0]:
                    zeros = [count, match.start(1)]

            count, where = zeros
            if count:
                quadc = quadc[:where] + ':' + quadc[where + count:]

            quadc = re.sub(r'((^:)|(:$))', '', quadc)
            quadc = re.sub(r'((^:)|(:$))', '::', quadc)

            return quadc

    setattr(ipcalc.IP, 'to_compressed', to_compressed)


def in_network(address, network, mask=None):
    ''' Return true if address is in network. '''
    return address in ipcalc.Network(network, mask=mask)


def is_ipv4(address):
    ''' Return true if address is an IPv4 one. '''
    return ipcalc.Network(address).version() == 4


def is_ipv6(address):
    ''' Return true if address is an IPv6 one. '''
    return ipcalc.Network(address).version() == 6


def address(address):
    ''' Return the address part. '''
    ip = ipcalc.IP(address)
    if ip.version() == 4:
        return ip
    else:
        return ip.to_compressed()


def mask(address):
    ''' Return the mask part. '''
    return ipcalc.Network(address).mask


class FilterModule(object):
    ''' Utility filters for operating on network addresses. '''

    def filters(self):
        return {
            'in_network': in_network,
            'is_ipv4': is_ipv4,
            'is_ipv6': is_ipv6,
            'address': address,
            'mask': mask,
        }
