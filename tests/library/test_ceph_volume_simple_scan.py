from mock.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import json
import os
import pytest
import sys
sys.path.append('./library')
import ceph_volume_simple_scan  # noqa : E402

fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'quay.ceph.io/ceph/daemon:latest'
fake_path = '/var/lib/ceph/osd/ceph-0'


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


class TestCephVolumeSimpleScanModule(object):

    @patch.object(basic.AnsibleModule, 'exit_json')
    def test_with_check_mode(self, m_exit_json):
        set_module_args({
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = exit_json

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'scan']
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch.object(basic.AnsibleModule, 'exit_json')
    @patch.object(basic.AnsibleModule, 'run_command')
    def test_with_failure(self, m_run_command, m_exit_json):
        set_module_args({
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = 'error'
        rc = 2
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'scan']
        assert result['rc'] == rc
        assert result['stderr'] == stderr

    @patch.object(basic.AnsibleModule, 'exit_json')
    @patch.object(basic.AnsibleModule, 'run_command')
    def test_scan_all_osds(self, m_run_command, m_exit_json):
        set_module_args({
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'scan']
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.object(os.path, 'exists', return_value=True)
    @patch.object(basic.AnsibleModule, 'exit_json')
    @patch.object(basic.AnsibleModule, 'run_command')
    def test_scan_path_exists(self, m_run_command, m_exit_json, m_os_path):
        set_module_args({
            'path': fake_path
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'scan', fake_path]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.object(os.path, 'exists', return_value=False)
    @patch.object(basic.AnsibleModule, 'fail_json')
    def test_scan_path_not_exists(self, m_fail_json, m_os_path):
        set_module_args({
            'path': fake_path
        })
        m_fail_json.side_effect = fail_json

        with pytest.raises(AnsibleFailJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert result['msg'] == '{} does not exist'.format(fake_path)
        assert result['rc'] == 1

    @patch.object(os.path, 'exists', return_value=True)
    @patch.object(basic.AnsibleModule, 'exit_json')
    @patch.object(basic.AnsibleModule, 'run_command')
    def test_scan_path_stdout_force(self, m_run_command, m_exit_json, m_os_path):
        set_module_args({
            'path': fake_path,
            'force': True,
            'stdout': True
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'scan', '--force', '--stdout', fake_path]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    @patch.object(basic.AnsibleModule, 'exit_json')
    @patch.object(basic.AnsibleModule, 'run_command')
    def test_scan_with_container(self, m_run_command, m_exit_json):
        set_module_args({
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

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
                                 '--cluster', fake_cluster, 'simple', 'scan']
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout
