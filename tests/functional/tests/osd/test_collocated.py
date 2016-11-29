import os
import pytest
import subprocess


uses_collocated_journals = pytest.mark.skipif(
    'collocated_journals' not in pytest.config.slaveinput['node_config']['components'],
    reason="only run in osds with collocated journals"
)

# XXX These could/should probably move to fixtures


def which(executable):
    locations = (
        '/usr/local/bin',
        '/bin',
        '/usr/bin',
        '/usr/local/sbin',
        '/usr/sbin',
        '/sbin',
    )

    for location in locations:
        executable_path = os.path.join(location, executable)
        if os.path.exists(executable_path):
            return executable_path


def get_system_devices():
    """
    uses ceph-disk to get a list of devices of a system, and formats the output nicely
    so that tests can consume it to make assertions:

    From:

        /dev/sda :
         /dev/sda2 other, 0x5
         /dev/sda5 other, LVM2_member
         /dev/sda1 other, ext2, mounted on /boot
        /dev/sdb :
         /dev/sdb1 ceph data, active, cluster ceph, osd.0, journal /dev/sdc1
        /dev/sdc :
         /dev/sdc1 ceph journal, for /dev/sdb1
        /dev/sr0 other, unknown

    To:

         {"/dev/sda2": "other, 0x5",
         "/dev/sda5": "other, LVM2_member",
         "/dev/sda1":  "other, ext2, mounted on /boot",
         "/dev/sdb1": "ceph data, active, cluster ceph, osd.0, journal /dev/sdc1",
         "/dev/sdc1": "ceph journal, for /dev/sdb1",
         "/dev/sr0":  "other, unknown"}
    """
    cmd = ['sudo', which('ceph-disk'), 'list']
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True
    )
    stdout = process.stdout.read().splitlines()
    stderr = process.stderr.read().splitlines()
    returncode = process.wait()
    if not stdout:
        raise RuntimeError("'ceph-disk list' failed with: %s" % ' '.join(stderr))

    device_map = {}

    for line in stdout:
        dev, comment = line.strip().split(' ', 1)
        if line.endswith(':'):
            continue
        device_map[dev] = comment

    return device_map


# XXX This test needs to be revisited. The loops obfuscate the values. They
# could very well be parametrized
class TestOSD(object):

    @uses_collocated_journals
    def test_osds_are_all_collocated(self, node_config):
        system_devices = get_system_devices()
        devices = node_config.get('devices', [])
        for device in devices:
            osd_devices = dict((d, comment) for d, comment in system_devices.items() if d.startswith(device))
            journal = dict((d, comment) for d, comment in osd_devices.items() if 'ceph journal' in comment)
            osd = dict((d, comment) for d, comment in osd_devices.items() if 'ceph data' in comment)
            assert journal != {}, 'no journal found for device: %s' % device
            assert osd != {}, 'no osd found for device: %s' % device
