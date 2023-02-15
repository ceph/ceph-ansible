import sys
import mock
import os
import pytest
import ca_test_common
sys.path.append('./library')
import ceph_volume  # noqa: E402


# Python 3
try:
    from unittest.mock import MagicMock, patch
except ImportError:
    # Python 2
    try:
        from mock import MagicMock, patch
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
        fake_container_image = "quay.io/ceph/daemon:latest"
        expected_command_list = get_container_cmd() + [fake_container_image]
        result = ceph_volume.container_exec(fake_binary, fake_container_image)
        assert result == expected_command_list

    def test_zap_osd_container(self):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda'}
        fake_container_image = "quay.io/ceph/daemon:latest"
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
        fake_container_image = "quay.io/ceph/daemon:latest"
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
        fake_container_image = "quay.io/ceph/daemon:latest"
        expected_command_list = get_container_cmd() + \
            [fake_container_image,
                '--cluster',
                'ceph',
                'inventory',
                '--format=json']
        result = ceph_volume.list_storage_inventory(fake_module, fake_container_image)
        assert result == expected_command_list

    @pytest.mark.parametrize('objectstore', ['bluestore'])
    def test_create_osd_container(self, objectstore):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': objectstore,
                              'cluster': 'ceph', }

        fake_action = "create"
        fake_container_image = "quay.io/ceph/daemon:latest"
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

    @pytest.mark.parametrize('objectstore', ['bluestore'])
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

    @pytest.mark.parametrize('objectstore', ['bluestore'])
    def test_prepare_osd_container(self, objectstore):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': objectstore,
                              'cluster': 'ceph', }

        fake_action = "prepare"
        fake_container_image = "quay.io/ceph/daemon:latest"
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

    @pytest.mark.parametrize('objectstore', ['bluestore'])
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

    @pytest.mark.parametrize('objectstore', ['bluestore'])
    def test_batch_osd_container(self, objectstore):
        fake_module = MagicMock()
        fake_module.params = {'data': '/dev/sda',
                              'objectstore': objectstore,
                              'block_db_size': '4096',
                              'journal_size': '4096',
                              'cluster': 'ceph',
                              'batch_devices': ["/dev/sda", "/dev/sdb"]}

        fake_container_image = "quay.io/ceph/daemon:latest"
        expected_command_list = get_container_cmd() + \
            [fake_container_image,
                '--cluster',
                'ceph',
                'lvm',
                'batch',
                '--%s' % objectstore,
                '--yes',
                '--prepare',
                '--block-db-size',
                '4096',
                '/dev/sda',
                '/dev/sdb']
        result = ceph_volume.batch(
            fake_module, fake_container_image)
        assert result == expected_command_list

    @pytest.mark.parametrize('objectstore', ['bluestore'])
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
                                 '--block-db-size',
                                 '4096',
                                 '/dev/sda',
                                 '/dev/sdb']
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

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_prepare_no_keyring_in_output(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({'data': '/dev/sda',
                                        'objectstore': 'bluestore',
                                        'cluster': 'ceph',
                                        'action': 'prepare'})
        keyring = 'AQBqkhNhQDlqEhAAXKxu87L3Mh3mHY+agonKZA=='
        m_exit_json.side_effect = ca_test_common.exit_json
        list_rc = 0
        list_stderr = ''
        list_stdout = '{}'
        prepare_rc = 0
        prepare_stderr = """
    Running command: /usr/bin/ceph-authtool --gen-print-key
    Running command: /usr/bin/mount -t tmpfs tmpfs /var/lib/ceph/osd/ceph-0
    Running command: /usr/bin/chown -h ceph:ceph /dev/test_group/data-lv1
    Running command: /usr/bin/chown -R ceph:ceph /dev/dm-0
    Running command: /usr/bin/ln -s /dev/test_group/data-lv1 /var/lib/ceph/osd/ceph-1/block
     stderr: got monmap epoch 1
    Running command: /usr/bin/ceph-authtool /var/lib/ceph/osd/ceph-1/keyring --create-keyring --name osd.1 --add-key {}
     stdout: creating /var/lib/ceph/osd/ceph-1/keyring
    added entity osd.1 auth(key={})
""".format(keyring, keyring)
        prepare_stdout = ''
        m_run_command.side_effect = [
            (list_rc, list_stdout, list_stderr),
            (prepare_rc, prepare_stdout, prepare_stderr)
        ]

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_volume.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', 'ceph', 'lvm', 'prepare', '--bluestore', '--data', '/dev/sda']
        assert result['rc'] == 0
        assert keyring not in result['stderr']
        assert '*' * 8 in result['stderr']
        assert not result['stdout']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_batch_no_keyring_in_output(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({'batch_devices': ['/dev/sda'],
                                        'objectstore': 'bluestore',
                                        'cluster': 'ceph',
                                        'action': 'batch'})
        keyring = 'AQBUixJhnDF1NRAAhl2xrnmOHCCI/T+W6FjqmA=='
        m_exit_json.side_effect = ca_test_common.exit_json
        report_rc = 0
        report_stderr = ''
        report_stdout = '[{"data": "/dev/sda", "data_size": "50.00 GB", "encryption": "None"}]'
        batch_rc = 0
        batch_stderr = """
    Running command: /usr/bin/ceph-authtool --gen-print-key
    Running command: /usr/bin/mount -t tmpfs tmpfs /var/lib/ceph/osd/ceph-0
    Running command: /usr/bin/chown -h ceph:ceph /dev/ceph-863337c4-bef9-4b96-aaac-27cde8c42b8f/osd-block-b1d1036f-0d6e-493b-9d1a-6f6b96df64b1
    Running command: /usr/bin/chown -R ceph:ceph /dev/mapper/ceph--863337c4--bef9--4b96--aaac--27cde8c42b8f-osd--block--b1d1036f--0d6e--493b--9d1a--6f6b96df64b1
    Running command: /usr/bin/ln -s /dev/ceph-863337c4-bef9-4b96-aaac-27cde8c42b8f/osd-block-b1d1036f-0d6e-493b-9d1a-6f6b96df64b1 /var/lib/ceph/osd/ceph-0/block
     stderr: got monmap epoch 1
    Running command: /usr/bin/ceph-authtool /var/lib/ceph/osd/ceph-0/keyring --create-keyring --name osd.0 --add-key {}
     stdout: creating /var/lib/ceph/osd/ceph-0/keyring
    added entity osd.0 auth(key={})
""".format(keyring, keyring)
        batch_stdout = ''
        m_run_command.side_effect = [
            (report_rc, report_stdout, report_stderr),
            (batch_rc, batch_stdout, batch_stderr)
        ]

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_volume.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', 'ceph', 'lvm', 'batch', '--bluestore', '--yes', '/dev/sda']
        assert result['rc'] == 0
        assert keyring not in result['stderr']
        assert '*' * 8 in result['stderr']
        assert not result['stdout']
