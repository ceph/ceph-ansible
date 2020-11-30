from mock.mock import patch
import pytest
import ca_test_common
import cephadm_adopt

fake_cluster = 'ceph'
fake_image = 'quay.ceph.io/ceph/daemon-base:latest'
fake_name = 'mon.foo01'


class TestCephadmAdoptModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_without_parameters(self, m_fail_json):
        ca_test_common.set_module_args({})
        m_fail_json.side_effect = ca_test_common.fail_json

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['msg'] == 'missing required arguments: name'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_name,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['cephadm', 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy']
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_failure(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_name
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = 'ERROR: cephadm should be run as root'
        rc = 1
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy']
        assert result['rc'] == 1
        assert result['stderr'] == 'ERROR: cephadm should be run as root'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_default_values(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_name
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = 'Stopping old systemd unit ceph-mon@{}...\n' \
                 'Disabling old systemd unit ceph-mon@{}...\n' \
                 'Moving data...\n' \
                 'Chowning content...\n' \
                 'Moving logs...\n' \
                 'Creating new units...\n' \
                 'firewalld ready'.format(fake_name, fake_name)
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy']
        assert result['rc'] == 0
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_docker(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_name,
            'docker': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', '--docker', 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_custom_image(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_name,
            'image': fake_image
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', '--image', fake_image, 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_without_pull(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_name,
            'pull': False
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy', '--skip-pull']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_without_firewalld(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_name,
            'firewalld': False
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy', '--skip-firewalld']
        assert result['rc'] == 0
