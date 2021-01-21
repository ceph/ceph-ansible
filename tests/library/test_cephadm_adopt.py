from mock.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import json
import pytest
import cephadm_adopt

fake_cluster = 'ceph'
fake_image = 'quay.ceph.io/ceph/daemon-base:latest'
fake_name = 'mon.foo01'


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


class TestCephadmAdoptModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_without_parameters(self, m_fail_json):
        set_module_args({})
        m_fail_json.side_effect = fail_json

        with pytest.raises(AnsibleFailJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['msg'] == 'missing required arguments: name'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        set_module_args({
            'name': fake_name,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = exit_json

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['cephadm', 'ls', '--no-detail']
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_failure(self, m_run_command, m_exit_json):
        set_module_args({
            'name': fake_name
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = 'ERROR: cephadm should be run as root'
        rc = 1
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['rc'] == 1
        assert result['msg'] == 'ERROR: cephadm should be run as root'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_default_values(self, m_run_command, m_exit_json):
        set_module_args({
            'name': fake_name
        })
        m_exit_json.side_effect = exit_json
        stdout = 'Stopping old systemd unit ceph-mon@{}...\n' \
                 'Disabling old systemd unit ceph-mon@{}...\n' \
                 'Moving data...\n' \
                 'Chowning content...\n' \
                 'Moving logs...\n' \
                 'Creating new units...\n' \
                 'firewalld ready'.format(fake_name, fake_name)
        stderr = ''
        rc = 0
        m_run_command.side_effect = [
            (0, '[{{"style":"legacy","name":"{}"}}]'.format(fake_name), ''),
            (rc, stdout, stderr)
        ]

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy']
        assert result['rc'] == 0
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_already_adopted(self, m_run_command, m_exit_json):
        set_module_args({
            'name': fake_name
        })
        m_exit_json.side_effect = exit_json
        stderr = ''
        stdout = '[{{"style":"cephadm:v1","name":"{}"}}]'.format(fake_name)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['cephadm', 'ls', '--no-detail']
        assert result['rc'] == 0
        assert result['stderr'] == stderr
        assert result['stdout'] == '{} is already adopted'.format(fake_name)

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_docker(self, m_run_command, m_exit_json):
        set_module_args({
            'name': fake_name,
            'docker': True
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.side_effect = [
            (0, '[{{"style":"legacy","name":"{}"}}]'.format(fake_name), ''),
            (rc, stdout, stderr)
        ]

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', '--docker', 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_custom_image(self, m_run_command, m_exit_json):
        set_module_args({
            'name': fake_name,
            'image': fake_image
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.side_effect = [
            (0, '[{{"style":"legacy","name":"{}"}}]'.format(fake_name), ''),
            (rc, stdout, stderr)
        ]

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', '--image', fake_image, 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_without_pull(self, m_run_command, m_exit_json):
        set_module_args({
            'name': fake_name,
            'pull': False
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.side_effect = [
            (0, '[{{"style":"legacy","name":"{}"}}]'.format(fake_name), ''),
            (rc, stdout, stderr)
        ]

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy', '--skip-pull']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_without_firewalld(self, m_run_command, m_exit_json):
        set_module_args({
            'name': fake_name,
            'firewalld': False
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.side_effect = [
            (0, '[{{"style":"legacy","name":"{}"}}]'.format(fake_name), ''),
            (rc, stdout, stderr)
        ]

        with pytest.raises(AnsibleExitJson) as result:
            cephadm_adopt.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['cephadm', 'adopt', '--cluster', fake_cluster, '--name', fake_name, '--style', 'legacy', '--skip-firewalld']
        assert result['rc'] == 0
