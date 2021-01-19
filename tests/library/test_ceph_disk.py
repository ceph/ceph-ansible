from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from mock.mock import patch
import json
import os
import pytest
import ceph_disk

fake_cluster = 'ceph'
fake_container_image = 'docker.io/ceph/daemon:latest'
fake_data = '/dev/sdb'
fake_journal = '/dev/sdc'
fake_block_db = '/dev/sdc'
fake_block_wal = '/dev/nvme0n1'


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


def exit_json(*args, **kwargs):
    raise AnsibleExitJson(kwargs)


class TestCephDiskModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        set_module_args({
            'data': fake_data,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = exit_json

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['rc'] == 0
        assert result['stdout'] == ''
        assert result['stderr'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('objstore', ['filestore', 'bluestore'])
    def test_prepare_osd(self, m_run_command, m_exit_json, objstore):
        set_module_args({
            'cluster': fake_cluster,
            'objectstore': objstore,
            'data': fake_data,
            'action': 'prepare'
        })
        m_exit_json.side_effect = exit_json
        m_run_command.return_value = 0, '', ''

        cmd = ['ceph-disk', 'prepare', '--cluster', fake_cluster, '--{}'.format(objstore), fake_data]

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('objstore', ['filestore', 'bluestore'])
    def test_prepare_osd_dmcrypt(self, m_run_command, m_exit_json, objstore):
        set_module_args({
            'cluster': fake_cluster,
            'objectstore': objstore,
            'data': fake_data,
            'dmcrypt': True,
            'action': 'prepare'
        })
        m_exit_json.side_effect = exit_json
        m_run_command.return_value = 0, '', ''

        cmd = ['ceph-disk', 'prepare', '--cluster', fake_cluster, '--{}'.format(objstore), fake_data, '--dmcrypt']

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_prepare_osd_filestore_journal(self, m_run_command, m_exit_json):
        set_module_args({
            'cluster': fake_cluster,
            'objectstore': 'filestore',
            'data': fake_data,
            'journal': fake_journal,
            'action': 'prepare'
        })
        m_exit_json.side_effect = exit_json
        m_run_command.return_value = 0, '', ''

        cmd = ['ceph-disk', 'prepare', '--cluster', fake_cluster, '--filestore', fake_data, fake_journal]

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_prepare_osd_bluestore_db_wal(self, m_run_command, m_exit_json):
        set_module_args({
            'cluster': fake_cluster,
            'objectstore': 'bluestore',
            'data': fake_data,
            'db': fake_block_db,
            'wal': fake_block_wal,
            'action': 'prepare'
        })
        m_exit_json.side_effect = exit_json
        m_run_command.return_value = 0, '', ''

        cmd = ['ceph-disk', 'prepare', '--cluster', fake_cluster, '--bluestore', '--block.db', fake_block_db, '--block.wal', fake_block_wal, fake_data]

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_activate_osd(self, m_run_command, m_exit_json):
        set_module_args({
            'cluster': fake_cluster,
            'data': '{}1'.format(fake_data),
            'action': 'activate'
        })
        m_exit_json.side_effect = exit_json
        m_run_command.return_value = 0, '', ''

        cmd = ['ceph-disk', 'activate', '{}1'.format(fake_data)]

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_activate_osd_dmcrypt(self, m_run_command, m_exit_json):
        set_module_args({
            'cluster': fake_cluster,
            'data': '{}1'.format(fake_data),
            'dmcrypt': True,
            'action': 'activate'
        })
        m_exit_json.side_effect = exit_json
        m_run_command.return_value = 0, '', ''

        cmd = ['ceph-disk', 'activate', '{}1'.format(fake_data), '--dmcrypt']

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_activate_osd_container(self, m_run_command, m_exit_json):
        set_module_args({
            'cluster': fake_cluster,
            'data': '{}1'.format(fake_data),
            'action': 'activate'
        })
        m_exit_json.side_effect = exit_json
        m_run_command.return_value = 0, '', ''

        cmd = ['docker', 'run', '--rm', '--privileged', '--net=host', '--ipc=host',
               '--ulimit', 'nofile=1024:4096', '-v', '/var/run/udev/:/var/run/udev/:z',
               '-v', '/dev:/dev', '-v', '/etc/ceph:/etc/ceph:z',
               '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
               '-v', '/var/log/ceph/:/var/log/ceph/:z',
               '--entrypoint=ceph-disk', fake_container_image,
               'activate', '{}1'.format(fake_data), '--no-start-daemon']

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_list_osd(self, m_run_command, m_exit_json):
        set_module_args({
            'cluster': fake_cluster,
            'action': 'list'
        })
        m_exit_json.side_effect = exit_json
        m_run_command.return_value = 0, '', ''

        cmd = ['ceph-disk', 'list']

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_list_osd_data(self, m_run_command, m_exit_json):
        set_module_args({
            'cluster': fake_cluster,
            'data': fake_data,
            'action': 'list'
        })
        m_exit_json.side_effect = exit_json
        m_run_command.return_value = 0, '', ''

        cmd = ['ceph-disk', 'list', fake_data]

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_zap_osd(self, m_run_command, m_exit_json):
        set_module_args({
            'cluster': fake_cluster,
            'data': fake_data,
            'action': 'zap'
        })
        m_exit_json.side_effect = exit_json
        m_run_command.return_value = 0, '', ''

        cmd = ['ceph-disk', 'zap', fake_data]

        with pytest.raises(AnsibleExitJson) as result:
            ceph_disk.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == ''
