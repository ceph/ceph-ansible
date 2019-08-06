from . import ceph_volume
from ansible.compat.tests.mock import MagicMock


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

    def test_container_exec(sefl):
        fake_binary = "ceph-volume"
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = ['docker', 'run', '--rm', '--privileged', '--net=host', '--ipc=host',  # noqa E501
                                 '--ulimit', 'nofile=1024:4096',
                                 '-v', '/run/lock/lvm:/run/lock/lvm:z',
                                 '-v', '/var/run/udev/:/var/run/udev/:z',
                                 '-v', '/dev:/dev', '-v', '/etc/ceph:/etc/ceph:z',  # noqa E501
                                 '-v', '/run/lvm/lvmetad.socket:/run/lvm/lvmetad.socket',  # noqa E501
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph-volume',
                                 'docker.io/ceph/daemon:latest-luminous']
        result = ceph_volume.container_exec(fake_binary, fake_container_image)
        assert result == expected_command_list

    def test_zap_osd_container(self):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda'}
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = ['docker', 'run', '--rm', '--privileged', '--net=host', '--ipc=host',  # noqa E501
                                 '--ulimit', 'nofile=1024:4096',
                                 '-v', '/run/lock/lvm:/run/lock/lvm:z',
                                 '-v', '/var/run/udev/:/var/run/udev/:z',
                                 '-v', '/dev:/dev', '-v', '/etc/ceph:/etc/ceph:z',  # noqa E501
                                 '-v', '/run/lvm/lvmetad.socket:/run/lvm/lvmetad.socket',  # noqa E501
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph-volume',
                                 'docker.io/ceph/daemon:latest-luminous',
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
                                 'lvm',
                                 'zap',
                                 '--destroy',
                                 '--osd-fsid',
                                 'a_uuid']
        result = ceph_volume.zap_devices(fake_module, fake_container_image)
        assert result == expected_command_list

    def test_activate_osd(self):
        expected_command_list = ['ceph-volume',
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
                                 '--format=json',
                                 ]
        result = ceph_volume.list_osd(fake_module, fake_container_image)
        assert result == expected_command_list

    def test_list_osd_container(self):
        fake_module = MagicMock()
        fake_module.params = {'cluster': 'ceph', 'data': '/dev/sda'}
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = ['docker', 'run', '--rm', '--privileged', '--net=host', '--ipc=host',  # noqa E501
                                 '--ulimit', 'nofile=1024:4096',
                                 '-v', '/run/lock/lvm:/run/lock/lvm:z',
                                 '-v', '/var/run/udev/:/var/run/udev/:z',
                                 '-v', '/dev:/dev', '-v', '/etc/ceph:/etc/ceph:z',  # noqa E501
                                 '-v', '/run/lvm/lvmetad.socket:/run/lvm/lvmetad.socket',  # noqa E501
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph-volume',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'list',
                                 '/dev/sda',
                                 '--format=json',
                                 ]
        result = ceph_volume.list_osd(fake_module, fake_container_image)
        assert result == expected_command_list

    def test_create_osd_container(self):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': 'filestore',
                              'cluster': 'ceph', }

        fake_action = "create"
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = ['docker', 'run', '--rm', '--privileged', '--net=host', '--ipc=host',  # noqa E501
                                 '--ulimit', 'nofile=1024:4096',
                                 '-v', '/run/lock/lvm:/run/lock/lvm:z',
                                 '-v', '/var/run/udev/:/var/run/udev/:z',
                                 '-v', '/dev:/dev', '-v', '/etc/ceph:/etc/ceph:z',  # noqa E501
                                 '-v', '/run/lvm/lvmetad.socket:/run/lvm/lvmetad.socket',  # noqa E501
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph-volume',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'create',
                                 '--filestore',
                                 '--data',
                                 '/dev/sda']
        result = ceph_volume.prepare_or_create_osd(
            fake_module, fake_action, fake_container_image)
        assert result == expected_command_list

    def test_create_osd(self):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': 'filestore',
                              'cluster': 'ceph', }

        fake_container_image = None
        fake_action = "create"
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'create',
                                 '--filestore',
                                 '--data',
                                 '/dev/sda']
        result = ceph_volume.prepare_or_create_osd(
            fake_module, fake_action, fake_container_image)
        assert result == expected_command_list

    def test_prepare_osd_container(self):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': 'filestore',
                              'cluster': 'ceph', }

        fake_action = "prepare"
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = ['docker', 'run', '--rm', '--privileged', '--net=host', '--ipc=host',  # noqa E501
                                 '--ulimit', 'nofile=1024:4096',
                                 '-v', '/run/lock/lvm:/run/lock/lvm:z',
                                 '-v', '/var/run/udev/:/var/run/udev/:z',
                                 '-v', '/dev:/dev', '-v', '/etc/ceph:/etc/ceph:z',  # noqa E501
                                 '-v', '/run/lvm/lvmetad.socket:/run/lvm/lvmetad.socket',  # noqa E501
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph-volume',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'prepare',
                                 '--filestore',
                                 '--data',
                                 '/dev/sda']
        result = ceph_volume.prepare_or_create_osd(
            fake_module, fake_action, fake_container_image)
        assert result == expected_command_list

    def test_prepare_osd(self):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': 'filestore',
                              'cluster': 'ceph', }

        fake_container_image = None
        fake_action = "prepare"
        expected_command_list = ['ceph-volume',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'prepare',
                                 '--filestore',
                                 '--data',
                                 '/dev/sda']
        result = ceph_volume.prepare_or_create_osd(
            fake_module, fake_action, fake_container_image)
        assert result == expected_command_list

    def test_batch_osd_container(self):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': 'filestore',
                              'journal_size': '100',
                              'cluster': 'ceph',
                              'batch_devices': ["/dev/sda", "/dev/sdb"]}

        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = ['docker', 'run', '--rm', '--privileged', '--net=host', '--ipc=host',  # noqa E501
                                 '--ulimit', 'nofile=1024:4096',
                                 '-v', '/run/lock/lvm:/run/lock/lvm:z',
                                 '-v', '/var/run/udev/:/var/run/udev/:z',
                                 '-v', '/dev:/dev', '-v', '/etc/ceph:/etc/ceph:z',  # noqa E501
                                 '-v', '/run/lvm/lvmetad.socket:/run/lvm/lvmetad.socket',  # noqa E501
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph-volume',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '--cluster',
                                 'ceph',
                                 'lvm',
                                 'batch',
                                 '--filestore',
                                 '--yes',
                                 '--prepare',
                                 '--journal-size',
                                 '100',
                                 '/dev/sda',
                                 '/dev/sdb']
        result = ceph_volume.batch(
            fake_module, fake_container_image)
        assert result == expected_command_list

    def test_batch_osd(self):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': 'filestore',
                              'journal_size': '100',
                              'cluster': 'ceph',
                              'batch_devices': ["/dev/sda", "/dev/sdb"]}

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
                                 '/dev/sdb']
        result = ceph_volume.batch(
            fake_module, fake_container_image)
        assert result == expected_command_list
