fake_fsid = "97e40ff4-97d7-4dc6-8bf5-bad598480621"

ansible_devices = {
    "nvme0n1": {
        "holders": [],
        "host": "Non-Volatile memory controller: Intel Corporation PCIe Data Center SSD (rev 01)",
                "links": {
                    "ids": [
                        "lvm-pv-uuid-XN7bf3-l0QX-CEAi-cnWl-3QL5-FmeI-DhpLTO",
                        "nvme-INTEL_SSDPEDMD400G4_CVFT623300HY400BGN",
                        "nvme-nvme.8086-43564654363233333030485934303042474e-494e54454c205353445045444d443430304734-00000001"
                    ],
                    "labels": [],
                    "masters": [],
                    "uuids": []
        },
        "model": "INTEL SSDPEDMD400G4",
        "partitions": {},
        "removable": "0",
        "rotational": "0",
        "sas_address": "",
        "sas_device_handle": "",
        "scheduler_mode": "",
        "sectors": "781422768",
        "sectorsize": "512",
        "size": "372.61 GB",
                "support_discard": "512",
                "vendor": "",
                "virtual": 1
    },
    "sda": {
        "holders": [],
        "host": "SATA controller: Intel Corporation C610/X99 series chipset 6-Port SATA Controller [AHCI mode] (rev 05)",
                "links": {
                    "ids": [
                        "ata-ST1000NM0033-9ZM173_Z1W5XGTA",
                        "wwn-0x5000c5009292d832"
                    ],
                    "labels": [],
                    "masters": [],
                    "uuids": []
        },
        "model": "ST1000NM0033-9ZM",
        "partitions": {
                    "sda1": {
                        "holders": [],
                        "links": {
                            "ids": [
                                "ata-ST1000NM0033-9ZM173_Z1W5XGTA-part1",
                                "wwn-0x5000c5009292d832-part1"
                            ],
                            "labels": [],
                            "masters": [],
                            "uuids": [
                                "37c255c5-6d3a-48fd-bcd7-732db11d680d"
                            ]
                        },
                        "sectors": "1953522688",
                        "sectorsize": 512,
                        "size": "931.51 GB",
                        "start": "2048",
                        "uuid": "37c255c5-6d3a-48fd-bcd7-732db11d680d"
                    }
        },
        "removable": "0",
        "rotational": "1",
        "sas_address": "",
        "sas_device_handle": "",
        "scheduler_mode": "cfq",
        "sectors": "1953525168",
        "sectorsize": "512",
        "size": "931.51 GB",
                "support_discard": "0",
                "vendor": "ATA",
                "virtual": 1,
                "wwn": "0x5000c5009292d832"
    }
}


def prepare_test_select_only_free_devices():
    return {'nvme0n1': {'bdev': '/dev/nvme0n1',
                        'holders': [],
                        'host': 'Non-Volatile memory controller: Intel Corporation PCIe Data Center SSD (rev 01)',
                        'links': {'ids': ['lvm-pv-uuid-XN7bf3-l0QX-CEAi-cnWl-3QL5-FmeI-DhpLTO',
                                          'nvme-INTEL_SSDPEDMD400G4_CVFT623300HY400BGN',
                                          'nvme-nvme.8086-43564654363233333030485934303042474e-494e54454c205353445045444d443430304734-00000001'],
                                  'labels': [],
                                  'masters': [],
                                  'uuids': []},
                        'model': 'INTEL SSDPEDMD400G4',
                        'partitions': {},
                        'removable': '0',
                        'rotational': '0',
                        'sas_address': '',
                        'sas_device_handle': '',
                        'scheduler_mode': '',
                        'sectors': '781422768',
                        'sectorsize': '512',
                        'size': '372.61 GB',
                        'support_discard': '512',
                        'vendor': '',
                        'virtual': 1}}


def read_ceph_disk(container_image=None):
    return [{"path": "/dev/nvme0n1", "type": "other", "dmcrypt": {}, "ptype": "unknown", "is_partition": False}, {"path": "/dev/sda", "partitions": [{"dmcrypt": {}, "uuid": "", "mount": "/", "ptype": "0x83", "is_partition": True, "fs_type": "ext4", "path": "/dev/sda1", "type": "other"}]}]


def is_read_only_device(physical_disk):
    devices = {"nvme0n1": False, "sda": False}
    if physical_disk in devices:
        return devices[physical_disk]
    else:
        exit("unexpected {} in is_read_only_device()".format(physical_disk))


def get_ceph_volume_lvm_list(partition, container_image=None):
    partitions = {}
    empty_answers = ["nvme0n1", "sda1"]
    for empty_answer in empty_answers:
        partitions["/dev/{}".format(empty_answer)] = {}

    if partition in partitions:
        return partitions[partition]
    else:
        exit("unexpected {} in get_ceph_volume_lvm_list()".format(partition))


def is_invalid_partition_table(partition):
    partitions = {}
    partitions["/dev/nvme0n1"] = "Error: /dev/nvme0n1: unrecognised disk label"
    partitions["/dev/sda1"] = "/dev/sda1:1000GB:unknown:512:512:loop:Unknown:;"
    if partition in partitions:
        if 'unrecognised disk label' not in partitions[partition].lower():
            if "error:" in partitions[partition].lower():
                return "failed"

        return ""
    else:
        exit("unexpected {} in is_valid_partition_table()".format(partition))


def get_partition_label(partition):
    partitions = {}
    empty_answers = ["nvme0n1", "sda1"]
    for empty_answer in empty_answers:
        partitions["/dev/{}".format(empty_answer)] = ""
    if partition in partitions:
        return partitions[partition]
    else:
        exit("unexpected {} in get_partition_label()".format(partition))


def is_lvm_disk(physical_disk):
    physical_disks = {}
    physical_disks["nvme0n1"] = False
    if physical_disk in physical_disks:
        return physical_disks[physical_disk]
    else:
        exit("unexpected {} in is_lvm_disk()".format(physical_disk))


def is_locked_raw_device(physical_disk):
    physical_disks = {}
    physical_disks["nvme0n1"] = False
    if physical_disk in physical_disks:
        return physical_disks[physical_disk]
    else:
        exit("unexpected {} in is_locked_raw_device()".format(physical_disk))
