from mock.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import json
import pytest
import cephadm_bootstrap

fake_fsid = '0f1e0605-db0b-485c-b366-bd8abaa83f3b'
fake_image = 'quay.ceph.io/ceph/daemon-base:latest-master-devel'
fake_ip = '192.168.42.1'


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


class TestCephadmBootstrapModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_without_parameters(self, m_fail_json):
        set_module_args({})
        m_fail_json.side_effect = fail_json

        with pytest.raises(AnsibleFailJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['msg'] == 'missing required arguments: mon_ip'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = exit_json

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['cephadm', 'bootstrap', '--mon-ip', fake_ip]
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_failure(self, m_run_command, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = 'ERROR: cephadm should be run as root'
        rc = 1
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'bootstrap', '--mon-ip', fake_ip]
        assert result['rc'] == 1
        assert result['stderr'] == 'ERROR: cephadm should be run as root'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_default_values(self, m_run_command, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip
        })
        m_exit_json.side_effect = exit_json
        stdout = 'Bootstrap complete.'
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'bootstrap', '--mon-ip', fake_ip]
        assert result['rc'] == 0
        assert result['stdout'] == 'Bootstrap complete.'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_docker(self, m_run_command, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip,
            'docker': True
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', '--docker', 'bootstrap', '--mon-ip', fake_ip]
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_custom_image(self, m_run_command, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip,
            'image': fake_image
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', '--image', fake_image, 'bootstrap', '--mon-ip', fake_ip]
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_custom_fsid(self, m_run_command, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip,
            'fsid': fake_fsid
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'bootstrap', '--mon-ip', fake_ip, '--fsid', fake_fsid]
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_without_pull(self, m_run_command, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip,
            'pull': False
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'bootstrap', '--mon-ip', fake_ip, '--skip-pull']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_dashboard_user_password(self, m_run_command, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip,
            'dashboard': True,
            'dashboard_user': 'foo',
            'dashboard_password': 'bar'
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'bootstrap', '--mon-ip', fake_ip, '--initial-dashboard-user', 'foo', '--initial-dashboard-password', 'bar']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_without_dashboard(self, m_run_command, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip,
            'dashboard': False
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'bootstrap', '--mon-ip', fake_ip, '--skip-dashboard']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_without_monitoring(self, m_run_command, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip,
            'monitoring': False
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'bootstrap', '--mon-ip', fake_ip, '--skip-monitoring-stack']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_without_firewalld(self, m_run_command, m_exit_json):
        set_module_args({
            'mon_ip': fake_ip,
            'firewalld': False
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_bootstrap.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'bootstrap', '--mon-ip', fake_ip, '--skip-firewalld']
        assert result['rc'] == 0
