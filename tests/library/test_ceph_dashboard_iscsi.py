from mock.mock import patch
import os
import pytest
import ca_test_common
import ceph_dashboard_iscsi

fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'quay.ceph.io/ceph/daemon:latest'
fake_gw_url = 'https://foo:bar@192.168.42.100:5000'
fake_gw_name = 'iscsigw01'
fake_user = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_user)


class TestCephDashboardiSCSIModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        ca_test_common.set_module_args({
            'url': fake_gw_url,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_dashboard_iscsi.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_add_iscsi_gateway(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'url': fake_gw_url,
            'name': fake_gw_name
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_run_command.side_effect = [
            (0, '{"gateways": {}}', ''),
            (0, 'Success', ''),
        ]
        cmd = ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'dashboard', 'iscsi-gateway-add', '-i', '-', fake_gw_name]

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_dashboard_iscsi.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == 'Success'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_add_iscsi_gateway_container(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'url': fake_gw_url,
            'name': fake_gw_name
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_run_command.side_effect = [
            (0, '{"gateways": {}}', ''),
            (0, 'Success', ''),
        ]
        cmd = [fake_container_binary, 'run', '--interactive',
               '--rm', '--net=host',
               '-v', '/etc/ceph:/etc/ceph:z',
               '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
               '-v', '/var/log/ceph/:/var/log/ceph/:z',
               '--entrypoint=ceph', fake_container_image,
               '-n', fake_user, '-k', fake_keyring,
               '--cluster', fake_cluster,
               'dashboard', 'iscsi-gateway-add', '-i', '-', fake_gw_name]

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_dashboard_iscsi.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == 'Success'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_add_iscsi_gateway_already_exist(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'url': fake_gw_url
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        rc = 0
        stderr = ''
        stdout = '{{"gateways": {{"{}": {{"service_url": "{}"}}}}}}'.format(fake_gw_name, fake_gw_url)
        m_run_command.return_value = rc, stdout, stderr
        cmd = ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'dashboard', 'iscsi-gateway-list', '--format=json']

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_dashboard_iscsi.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_delete_iscsi_gateway(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_gw_name,
            'state': 'absent'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_run_command.side_effect = [
            (0, '{{"gateways": {{"{}": {{"service_url": "{}"}}}}}}'.format(fake_gw_name, fake_gw_url), ''),
            (0, 'Success', ''),
        ]
        cmd = ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'dashboard', 'iscsi-gateway-rm', fake_gw_name]

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_dashboard_iscsi.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == 'Success'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_delete_iscsi_gateway_not_exist(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_gw_name,
            'state': 'absent'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        rc = 0
        stderr = ''
        stdout = '{"gateways": {}}'
        m_run_command.return_value = rc, stdout, stderr
        cmd = ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'dashboard', 'iscsi-gateway-list', '--format=json']

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_dashboard_iscsi.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == "iSCSI gateway {} doesn't exist".format(fake_gw_name)
