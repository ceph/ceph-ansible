ansible_devices = {
        'sr0': {'scheduler_mode': 'cfq', 'sectorsize': '512', 'vendor': 'MATSHITA', 'sectors': '2097151', 'sas_device_handle': None, 'sas_address': None,
            'host': 'SATA controller: Intel Corporation 8 Series/C220 Series Chipset Family 6-port SATA Controller 1 [AHCI mode] (rev 04)',
            'rotational': '1', 'removable': '1', 'support_discard': '0', 'holders': [],
            'size': '1024.00 MB', 'model': 'DVD-RAM UJ8G2', 'partitions': {}
            },
        'sda': {'scheduler_mode': 'cfq', 'sectorsize': '512', 'vendor': 'ATA',
            'sectors': '1000215216', 'sas_device_handle': None, 'sas_address': None,
            'host': 'SATA controller: Intel Corporation 8 Series/C220 Series Chipset Family 6-port SATA Controller 1 [AHCI mode] (rev 04)',
            'rotational': '0', 'removable': '0', 'support_discard': '512', 'holders': [], 'size': '476.94 GB',
            'model': 'SAMSUNG MZ7LN512',
            'partitions': {
                'sda4': {'sectorsize': 512, 'uuid': None, 'sectors': '2', 'start': '663115776', 'holders': [], 'size': '1.00 KB'},
                'sda5': {'sectorsize': 512, 'uuid': 'daddc2c4-1463-4d46-abc7-b15770b79f94', 'sectors': '337096704', 'start': '663117824', 'holders': ['luks-daddc2c4-1463-4d46-abc7-b15770b79f94'], 'size': '160.74 GB'},
                'sda2': {'sectorsize': 512, 'uuid': 'c3d3ae17-1ece-432e-bb4b-f38bfa12e876', 'sectors': '629149696', 'start': '411648', 'holders': [], 'size': '300.00 GB'},
                'sda3': {'sectorsize': 512, 'uuid': '51f0126d-0d7f-4708-b8b8-f122ac8dcf46', 'sectors': '33554432',  'start': '629561344', 'holders': [], 'size': '16.00 GB'},
                'sda1': {'sectorsize': 512, 'uuid': '71adc8ce-fc61-419d-82d5-0faec6d97f60', 'sectors': '409600', 'start': '2048', 'holders': [], 'size': '200.00 MB'}
                }
            }
        }


def prepare_test_find_match_matched():
    disk_0 = {'storage_disks': {'model': 'SAMSUNG MZ7LN512', 'rotational': '0', 'ceph_type': 'data' }}
    expected_result = {
            'storage_disks': {'sectorsize': '512', 'vendor': 'ATA', 'sas_device_handle': None, 'host': 'SATA controller: Intel Corporation 8 Series/C220 Series Chipset Family 6-port SATA Controller 1 [AHCI mode] (rev 04)',
                'support_discard': '512', 'model': 'SAMSUNG MZ7LN512', 'size': '476.94 GB', 'scheduler_mode': 'cfq', 'rotational': '0', 'sectors': '1000215216', 'sas_address':  None,
                'removable': '0', 'holders': [],
                'partitions': {
                    'sda4': {'sectorsize': 512, 'uuid': None, 'sectors': '2', 'start': '663115776', 'holders': [], 'size': '1.00 KB'},
                    'sda5': {'sectorsize': 512, 'uuid': 'daddc2c4-1463-4d46-abc7-b15770b79f94', 'sectors': '337096704', 'start': '663117824', 'holders': ['luks-daddc2c4-1463-4d46-abc7-b15770b79f94'], 'size': '160.74 GB'},
                    'sda2': {'sectorsize': 512, 'uuid': 'c3d3ae17-1ece-432e-bb4b-f38bfa12e876', 'sectors': '629149696', 'start': '411648', 'holders': [], 'size': '300.00 GB'},
                    'sda3': {'sectorsize': 512, 'uuid': '51f0126d-0d7f-4708-b8b8-f122ac8dcf46', 'sectors': '33554432', 'start': '629561344', 'holders': [], 'size': '16.00 GB'},
                    'sda1': {'sectorsize': 512, 'uuid': '71adc8ce-fc61-419d-82d5-0faec6d97f60', 'sectors': '409600', 'start': '2048', 'holders': [], 'size': '200.00 MB'}
                    },
                'ceph_type': 'data'
                }
            }

    return (disk_0, expected_result)


def prepare_test_find_match_unmatched():
    return({'storage_disks_0': {'model': 'SAMSUNG MZ7LN512', 'rotational': '1'}}, {})
