from mock.mock import patch
import os
import pytest
import ca_test_common
import ceph_volume_simple_scan

fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'quay.io/ceph/daemon:latest'
fake_path = '/var/lib/ceph/osd/ceph-0'


class TestCephVolumeSimpleScanModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        ca_test_common.set_module_args({
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'scan']
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_failure(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = 'error'
        rc = 2
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'scan']
        assert result['rc'] == rc
        assert result['stderr'] == stderr

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_scan_all_osds(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'scan']
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.object(os.path, 'exists', return_value=True)
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_scan_path_exists(self, m_run_command, m_exit_json, m_os_path):
        ca_test_common.set_module_args({
            'path': fake_path
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'scan', fake_path]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.object(os.path, 'exists', return_value=False)
    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_scan_path_not_exists(self, m_fail_json, m_os_path):
        ca_test_common.set_module_args({
            'path': fake_path
        })
        m_fail_json.side_effect = ca_test_common.fail_json

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert result['msg'] == '{} does not exist'.format(fake_path)
        assert result['rc'] == 1

    @patch.object(os.path, 'exists', return_value=True)
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_scan_path_stdout_force(self, m_run_command, m_exit_json, m_os_path):
        ca_test_common.set_module_args({
            'path': fake_path,
            'force': True,
            'stdout': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_volume_simple_scan.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph-volume', '--cluster', fake_cluster, 'simple', 'scan', '--force', '--stdout', fake_path]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_scan_with_container(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
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
