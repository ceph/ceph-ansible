from mock.mock import patch
import os
import pytest
import ca_test_common
import ceph_mgr_module

fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'quay.ceph.io/ceph/daemon:latest'
fake_module = 'noup'
fake_user = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_user)


class TestCephMgrModuleModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_without_parameters(self, m_fail_json):
        ca_test_common.set_module_args({})
        m_fail_json.side_effect = ca_test_common.fail_json

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert result['msg'] == 'missing required arguments: name'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_module,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'mgr', 'module', 'enable', fake_module]
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_failure(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_module
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = 'Error ENOENT: all mgr daemons do not support module \'{}\', pass --force to force enablement'.format(fake_module)
        rc = 2
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'mgr', 'module', 'enable', fake_module]
        assert result['rc'] == rc
        assert result['stderr'] == stderr

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_enable_module(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_module,
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'mgr', 'module', 'enable', fake_module]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_already_enable_module(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_module,
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stderr = 'module \'{}\' is already enabled'.format(fake_module)
        stdout = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'mgr', 'module', 'enable', fake_module]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_disable_module(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_module,
            'state': 'disable'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'mgr', 'module', 'disable', fake_module]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_container(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_module,
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = '{} is set'.format(fake_module)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == [fake_container_binary, 'run', '--rm', '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph', fake_container_image,
                                 '-n', fake_user, '-k', fake_keyring,
                                 '--cluster', fake_cluster, 'mgr', 'module', 'enable', fake_module]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout
