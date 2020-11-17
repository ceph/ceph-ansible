from mock.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import json
import os
import pytest
import sys
sys.path.append('./library')
import ceph_volume_simple_activate  # noqa : E402

fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'quay.ceph.io/ceph/daemon:latest'
fake_id = '42'
fake_uuid = '0c4a7eca-0c2a-4c12-beff-08a80f064c52'
fake_path = '/etc/ceph/osd/{}-{}.json'.format(fake_id, fake_uuid)


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    raise AnsibleFailJson(kwargs)


class TestCephVolumeSimpleActivateModule(object):

    @patch.object(basic.AnsibleModule, 'exit_json')
    def test_with_check_mode(self, m_exit_json):
        set_module_args({
            'osd_id': fake_id,
            'osd_fsid': fake_uuid,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = exit_json

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_activate.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'activate', fake_id, fake_uuid]
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch.object(basic.AnsibleModule, 'exit_json')
    @patch.object(basic.AnsibleModule, 'run_command')
    def test_with_failure(self, m_run_command, m_exit_json):
        set_module_args({
            'osd_id': fake_id,
            'osd_fsid': fake_uuid
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = 'error'
        rc = 2
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_activate.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'activate', fake_id, fake_uuid]
        assert result['rc'] == rc
        assert result['stderr'] == stderr

    @patch.object(basic.AnsibleModule, 'exit_json')
    @patch.object(basic.AnsibleModule, 'run_command')
    def test_activate_all_osds(self, m_run_command, m_exit_json):
        set_module_args({
            'osd_all': True
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_activate.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'activate', '--all']
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.object(os.path, 'exists', return_value=True)
    @patch.object(basic.AnsibleModule, 'exit_json')
    @patch.object(basic.AnsibleModule, 'run_command')
    def test_activate_path_exists(self, m_run_command, m_exit_json, m_os_path):
        set_module_args({
            'path': fake_path
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_activate.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'activate', '--file', fake_path]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.object(os.path, 'exists', return_value=False)
    @patch.object(basic.AnsibleModule, 'fail_json')
    def test_activate_path_not_exists(self, m_fail_json, m_os_path):
        set_module_args({
            'path': fake_path
        })
        m_fail_json.side_effect = fail_json

        with pytest.raises(AnsibleFailJson) as result:
            ceph_volume_simple_activate.main()

        result = result.value.args[0]
        assert result['msg'] == '{} does not exist'.format(fake_path)
        assert result['rc'] == 1

    @patch.object(basic.AnsibleModule, 'exit_json')
    @patch.object(basic.AnsibleModule, 'run_command')
    def test_activate_without_systemd(self, m_run_command, m_exit_json):
        set_module_args({
            'osd_id': fake_id,
            'osd_fsid': fake_uuid,
            'systemd': False
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_activate.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'activate', fake_id, fake_uuid, '--no-systemd']
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    @patch.object(basic.AnsibleModule, 'exit_json')
    @patch.object(basic.AnsibleModule, 'run_command')
    def test_activate_with_container(self, m_run_command, m_exit_json):
        set_module_args({
            'osd_id': fake_id,
            'osd_fsid': fake_uuid,
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_activate.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == [fake_container_binary,
                                 'run', '--rm', '--privileged',
                                 '--ipc=host', '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '-v', '/run/lvm/:/run/lvm/',
                                 '-v', '/run/lock/lvm/:/run/lock/lvm/',
                                 '--entrypoint=ceph-volume', fake_container_image,
                                 '--cluster', fake_cluster, 'simple', 'activate', fake_id, fake_uuid]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout
