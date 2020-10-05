from mock.mock import patch
import os
import pytest
import ca_test_common
import ceph_dashboard_rgw

fake_binary = 'ceph'
fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'quay.ceph.io/ceph/daemon:latest'
fake_user_key = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_user_key)
ceph_common = '-n {} -k {} --cluster {} dashboard'.format(fake_user_key, fake_keyring, fake_cluster)
container_common = '--rm --net=host -v /etc/ceph:/etc/ceph:z' \
                   ' -v /var/lib/ceph/:/var/lib/ceph/:z -v /var/log/ceph/:/var/log/ceph/:z' \
                   ' --entrypoint={} {} {} '.format(fake_binary, fake_container_image, ceph_common)
fake_container_cmd = '{} run {}'.format(fake_container_binary, container_common)
fake_container_cmd_stdin = '{} run --interactive {}'.format(fake_container_binary, container_common)
fake_cmd = '{} {} '.format(fake_binary, ceph_common)
fake_user = 'foo'
fake_access_key = 'PC7NPg87QWhOzXTkXIhX'
fake_secret_key = 'jV64v39lVTjEx1ZJN6ocopnhvwMp1mXCD4kzBiPz'
fake_host = '192.168.100.1'
fake_port = 10080
fake_scheme = 'https'
fake_admin_resource = 'admin'
fake_tls_verify = False
fake_user_key = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_user_key)


class TestCephDashboardRGWModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        ca_test_common.set_module_args({
            'user': fake_user,
            'access_key': fake_access_key,
            'secret_key': fake_secret_key,
            'host': fake_host,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_dashboard_rgw.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_all_options(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'user': fake_user,
            'access_key': fake_access_key,
            'secret_key': fake_secret_key,
            'host': fake_host,
            'port': fake_port,
            'scheme': fake_scheme,
            'admin_resource': fake_admin_resource,
            'tls_verify': fake_tls_verify
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_run_command.side_effect = [
            (0, '', ''),
            (0, 'Option RGW_API_USER_ID updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_ACCESS_KEY updated', ''),
            (0, '', ''),
            (0, 'Option RGW_SECRET_KEY updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_HOST updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_PORT updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_SCHEME updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_ADMIN_RESOURCE updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_SSL_VERIFY updated', ''),
        ]

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_dashboard_rgw.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == [fake_cmd + 'set-rgw-api-user-id {}'.format(fake_user),
                                 fake_cmd + 'set-rgw-api-access-key -i -',
                                 fake_cmd + 'set-rgw-api-secret-key -i -',
                                 fake_cmd + 'set-rgw-api-host {}'.format(fake_host),
                                 fake_cmd + 'set-rgw-api-port {}'.format(fake_port),
                                 fake_cmd + 'set-rgw-api-scheme {}'.format(fake_scheme),
                                 fake_cmd + 'set-rgw-api-admin-resource {}'.format(fake_admin_resource),
                                 fake_cmd + 'set-rgw-api-ssl-verify {}'.format(fake_tls_verify)]
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == 'Option RGW_API_USER_ID updated' \
                                   'Option RGW_API_ACCESS_KEY updated' \
                                   'Option RGW_SECRET_KEY updated' \
                                   'Option RGW_API_HOST updated' \
                                   'Option RGW_API_PORT updated' \
                                   'Option RGW_API_SCHEME updated' \
                                   'Option RGW_API_ADMIN_RESOURCE updated' \
                                   'Option RGW_API_SSL_VERIFY updated'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_options_already_set(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'user': fake_user,
            'access_key': fake_access_key,
            'secret_key': fake_secret_key,
            'host': fake_host,
            'port': fake_port,
            'scheme': fake_scheme,
            'admin_resource': fake_admin_resource,
            'tls_verify': fake_tls_verify
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_run_command.side_effect = [
            (0, fake_user, ''),
            (0, fake_access_key, ''),
            (0, fake_secret_key, ''),
            (0, fake_host, ''),
            (0, str(fake_port), ''),
            (0, fake_scheme, ''),
            (0, fake_admin_resource, ''),
            (0, str(fake_tls_verify), ''),
        ]

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_dashboard_rgw.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == [fake_cmd + 'get-rgw-api-user-id',
                                 fake_cmd + 'get-rgw-api-access-key',
                                 fake_cmd + 'get-rgw-api-secret-key',
                                 fake_cmd + 'get-rgw-api-host',
                                 fake_cmd + 'get-rgw-api-port',
                                 fake_cmd + 'get-rgw-api-scheme',
                                 fake_cmd + 'get-rgw-api-admin-resource',
                                 fake_cmd + 'get-rgw-api-ssl-verify']
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == 'Nothing to update'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_with_containers(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'user': fake_user,
            'access_key': fake_access_key,
            'secret_key': fake_secret_key,
            'host': fake_host,
            'port': fake_port,
            'scheme': fake_scheme,
            'admin_resource': fake_admin_resource,
            'tls_verify': fake_tls_verify
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_run_command.side_effect = [
            (0, '', ''),
            (0, 'Option RGW_API_USER_ID updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_ACCESS_KEY updated', ''),
            (0, '', ''),
            (0, 'Option RGW_SECRET_KEY updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_HOST updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_PORT updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_SCHEME updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_ADMIN_RESOURCE updated', ''),
            (0, '', ''),
            (0, 'Option RGW_API_SSL_VERIFY updated', ''),
        ]

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_dashboard_rgw.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == [fake_container_cmd + 'set-rgw-api-user-id {}'.format(fake_user),
                                 fake_container_cmd_stdin + 'set-rgw-api-access-key -i -',
                                 fake_container_cmd_stdin + 'set-rgw-api-secret-key -i -',
                                 fake_container_cmd + 'set-rgw-api-host {}'.format(fake_host),
                                 fake_container_cmd + 'set-rgw-api-port {}'.format(fake_port),
                                 fake_container_cmd + 'set-rgw-api-scheme {}'.format(fake_scheme),
                                 fake_container_cmd + 'set-rgw-api-admin-resource {}'.format(fake_admin_resource),
                                 fake_container_cmd + 'set-rgw-api-ssl-verify {}'.format(fake_tls_verify)]
        assert result['rc'] == 0
        assert result['stderr'] == ''
        assert result['stdout'] == 'Option RGW_API_USER_ID updated' \
                                   'Option RGW_API_ACCESS_KEY updated' \
                                   'Option RGW_SECRET_KEY updated' \
                                   'Option RGW_API_HOST updated' \
                                   'Option RGW_API_PORT updated' \
                                   'Option RGW_API_SCHEME updated' \
                                   'Option RGW_API_ADMIN_RESOURCE updated' \
                                   'Option RGW_API_SSL_VERIFY updated'
