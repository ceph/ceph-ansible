import sys
import mock
import os
import pytest
sys.path.append('./library')
import ceph_volume  # noqa: E402


# Python 3
try:
    from unittest.mock import MagicMock
except ImportError:
    # Python 2
    try:
        from mock import MagicMock
    except ImportError:
        print('You need the mock library installed on python2.x to run tests')


def get_mounts(mounts=None):
    volumes = {}
    volumes['/run/lock/lvm'] = '/run/lock/lvm:z'
    volumes['/var/run/udev'] = '/var/run/udev:z'
    volumes['/dev'] = '/dev'
    volumes['/etc/ceph'] = '/etc/ceph:z'
    volumes['/run/lvm'] = '/run/lvm'
    volumes['/var/lib/ceph'] = '/var/lib/ceph:z'
    volumes['/var/log/ceph'] = '/var/log/ceph:z'
    if mounts is not None:
        volumes.update(mounts)

    return sum([['-v', '{}:{}'.format(src_dir, dst_dir)] for src_dir, dst_dir in volumes.items()], [])


def get_container_cmd(mounts=None):

    return ['docker', 'run', '--rm', '--privileged',
            '--net=host', '--ipc=host'] + \
            get_mounts(mounts) + ['--entrypoint=ceph-volume']


@mock.patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': 'docker'})
class TestCephVolumeModule(object):

    def test_data_no_vg(self):
        result = ceph_volume.get_data("/dev/sda", None)
        assert result == "/dev/sda"

    def test_data_with_vg(self):
        result = ceph_volume.get_data("data-lv", "data-vg")
        assert result == "data-vg/data-lv"

    def test_journal_no_vg(self):
        result = ceph_volume.get_journal("/dev/sda1", None)
        assert result == "/dev/sda1"

    def test_journal_with_vg(self):
        result = ceph_volume.get_journal("journal-lv", "journal-vg")
        assert result == "journal-vg/journal-lv"

    def test_db_no_vg(self):
        result = ceph_volume.get_db("/dev/sda1", None)
        assert result == "/dev/sda1"

    def test_db_with_vg(self):
        result = ceph_volume.get_db("db-lv", "db-vg")
        assert result == "db-vg/db-lv"

    def test_wal_no_vg(self):
        result = ceph_volume.get_wal("/dev/sda1", None)
        assert result == "/dev/sda1"

    def test_wal_with_vg(self):
        result = ceph_volume.get_wal("wal-lv", "wal-vg")
        assert result == "wal-vg/wal-lv"

    def test_container_exec(self):
        fake_binary = "ceph-volume"
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest"
        expected_command_list = get_container_cmd() + [fake_container_image]
        result = ceph_volume.container_exec(fake_binary, fake_container_image)
        assert result == expected_command_list

    def test_zap_osd_container(self):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda'}
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest"
        expected_command_list = get_container_cmd() + \
            [fake_container_image,
                '--cluster',
                'ceph',
                'lvm',
                'zap',
                '--destroy',
                '/dev/sda']
        result = ceph_volume.zap_devices(fake_module, fake_container_image)
        assert result == expected_command_list

    def test_zap_osd(self):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda'}
        fake_container_image = None
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'zap',
                                 '--destroy',
                                 '/dev/sda']
        result = ceph_volume.zap_devices(fake_module, fake_container_image)
        assert result == expected_command_list

    def test_zap_osd_fsid(self):
        fake_module = MagicMock()
        fake_module.params = {'osd_fsid': 'a_uuid'}
        fake_container_image = None
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'zap',
                                 '--destroy',
                                 '--osd-fsid',
                                 'a_uuid']
        result = ceph_volume.zap_devices(fake_module, fake_container_image)
        assert result == expected_command_list

    def test_zap_osd_id(self):
        fake_module = MagicMock()
        fake_module.params = {'osd_id': '123'}
        fake_container_image = None
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'zap',
                                 '--destroy',
                                 '--osd-id',
                                 '123']
        result = ceph_volume.zap_devices(fake_module, fake_container_image)
        assert result == expected_command_list

    def test_activate_osd(self):
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'activate',
                                 '--all']
        result = ceph_volume.activate_osd()
        assert result == expected_command_list

    def test_list_osd(self):
        fake_module = MagicMock()
        fake_module.params = {'cluster': 'ceph', 'data': '/dev/sda'}
        fake_container_image = None
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'list',
                                 '/dev/sda',
                                 '--format=json']
        result = ceph_volume.list_osd(fake_module, fake_container_image)
        assert result == expected_command_list

    def test_list_osd_container(self):
        fake_module = MagicMock()
        fake_module.params = {'cluster': 'ceph', 'data': '/dev/sda'}
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest"
        expected_command_list = get_container_cmd(
                                {
                                    '/var/lib/ceph': '/var/lib/ceph:ro'
                                }) + \
            [fake_container_image,
                '--cluster',
                'ceph',
                'lvm',
                'list',
                '/dev/sda',
                '--format=json']
        result = ceph_volume.list_osd(fake_module, fake_container_image)
        assert result == expected_command_list

    def test_list_storage_inventory(self):
        fake_module = MagicMock()
        fake_container_image = None
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'inventory',
                                 '--format=json',
                                 ]
        result = ceph_volume.list_storage_inventory(fake_module, fake_container_image)
        assert result == expected_command_list

    def test_list_storage_inventory_container(self):
        fake_module = MagicMock()
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest"
        expected_command_list = get_container_cmd() + \
            [fake_container_image,
                '--cluster',
                'ceph',
                'inventory',
                '--format=json']
        result = ceph_volume.list_storage_inventory(fake_module, fake_container_image)
        assert result == expected_command_list

    @pytest.mark.parametrize('objectstore', ['bluestore', 'filestore'])
    def test_create_osd_container(self, objectstore):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': objectstore,
                              'cluster': 'ceph', }

        fake_action = "create"
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest"
        expected_command_list = get_container_cmd() + \
            [fake_container_image,
                '--cluster',
                'ceph',
                'lvm',
                'create',
                '--%s' % objectstore,
                '--data',
                '/dev/sda']
        result = ceph_volume.prepare_or_create_osd(
            fake_module, fake_action, fake_container_image)
        assert result == expected_command_list

    @pytest.mark.parametrize('objectstore', ['bluestore', 'filestore'])
    def test_create_osd(self, objectstore):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': objectstore,
                              'cluster': 'ceph', }

        fake_container_image = None
        fake_action = "create"
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'create',
                                 '--%s' % objectstore,
                                 '--data',
                                 '/dev/sda']
        result = ceph_volume.prepare_or_create_osd(
            fake_module, fake_action, fake_container_image)
        assert result == expected_command_list

    @pytest.mark.parametrize('objectstore', ['bluestore', 'filestore'])
    def test_prepare_osd_container(self, objectstore):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': objectstore,
                              'cluster': 'ceph', }

        fake_action = "prepare"
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest"
        expected_command_list = get_container_cmd() + \
            [fake_container_image,
                '--cluster',
                'ceph',
                'lvm',
                'prepare',
                '--%s' % objectstore,
                '--data',
                '/dev/sda']
        result = ceph_volume.prepare_or_create_osd(
            fake_module, fake_action, fake_container_image)
        assert result == expected_command_list

    @pytest.mark.parametrize('objectstore', ['bluestore', 'filestore'])
    def test_prepare_osd(self, objectstore):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': objectstore,
                              'cluster': 'ceph', }

        fake_container_image = None
        fake_action = "prepare"
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'prepare',
                                 '--%s' % objectstore,
                                 '--data',
                                 '/dev/sda']
        result = ceph_volume.prepare_or_create_osd(
            fake_module, fake_action, fake_container_image)
        assert result == expected_command_list

    @pytest.mark.parametrize('objectstore', ['bluestore', 'filestore'])
    def test_batch_osd_container(self, objectstore):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': objectstore,
                              'block_db_size': '4096',
                              'journal_size': '4096',
                              'cluster': 'ceph',
                              'batch_devices': ["/dev/sda", "/dev/sdb"]}

        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest"
        expected_command_list = get_container_cmd() + \
            [fake_container_image,
                '--cluster',
                'ceph',
                'lvm',
                'batch',
                '--%s' % objectstore,
                '--yes',
                '--prepare',
                '--journal-size' if objectstore == 'filestore' else '--block-db-size',  # noqa E501
                '4096',
                '/dev/sda',
                '/dev/sdb']
        result = ceph_volume.batch(
            fake_module, fake_container_image)
        assert result == expected_command_list

    @pytest.mark.parametrize('objectstore', ['bluestore', 'filestore'])
    def test_batch_osd(self, objectstore):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': objectstore,
                              'block_db_size': '4096',
                              'journal_size': '4096',
                              'cluster': 'ceph',
                              'batch_devices': ["/dev/sda", "/dev/sdb"]}

        fake_container_image = None
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'batch',
                                 '--%s' % objectstore,
                                 '--yes',
                                 '--journal-size' if objectstore == 'filestore' else '--block-db-size',  # noqa E501
                                 '4096',
                                 '/dev/sda',
                                 '/dev/sdb']
        result = ceph_volume.batch(
            fake_module, fake_container_image)
        assert result == expected_command_list

    def test_batch_filestore_with_dedicated_journal(self):
        fake_module = MagicMock()
        fake_module.params = {'objectstore': 'filestore',
                              'journal_size': '100',
                              'cluster': 'ceph',
                              'batch_devices': ["/dev/sda", "/dev/sdb"],
                              'journal_devices': ["/dev/sdc", "/dev/sdd"]}

        fake_container_image = None
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'batch',
                                 '--filestore',
                                 '--yes',
                                 '--journal-size',
                                 '100',
                                 '/dev/sda',
                                 '/dev/sdb',
                                 '--journal-devices',
                                 '/dev/sdc',
                                 '/dev/sdd']
        result = ceph_volume.batch(
            fake_module, fake_container_image)
        assert result == expected_command_list

    def test_batch_bluestore_with_dedicated_db(self):
        fake_module = MagicMock()
        fake_module.params = {'objectstore': 'bluestore',
                              'block_db_size': '-1',
                              'cluster': 'ceph',
                              'batch_devices': ["/dev/sda", "/dev/sdb"],
                              'block_db_devices': ["/dev/sdc", "/dev/sdd"]}

        fake_container_image = None
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'batch',
                                 '--bluestore',
                                 '--yes',
                                 '/dev/sda',
                                 '/dev/sdb',
                                 '--db-devices',
                                 '/dev/sdc',
                                 '/dev/sdd']
        result = ceph_volume.batch(
            fake_module, fake_container_image)
        assert result == expected_command_list

    def test_batch_bluestore_with_dedicated_wal(self):
        fake_module = MagicMock()
        fake_module.params = {'objectstore': 'bluestore',
                              'cluster': 'ceph',
                              'block_db_size': '-1',
                              'batch_devices': ["/dev/sda", "/dev/sdb"],
                              'wal_devices': ["/dev/sdc", "/dev/sdd"]}

        fake_container_image = None
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'batch',
                                 '--bluestore',
                                 '--yes',
                                 '/dev/sda',
                                 '/dev/sdb',
                                 '--wal-devices',
                                 '/dev/sdc',
                                 '/dev/sdd']
        result = ceph_volume.batch(
            fake_module, fake_container_image)
        assert result == expected_command_list
