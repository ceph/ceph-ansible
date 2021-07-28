from mock.mock import MagicMock, patch
import pytest
import os
import ca_test_common
import ceph_dashboard_user

fake_container_binary = 'podman'
fake_container_image = 'docker.io/ceph/daemon:latest'


class TestCephDashboardUserModule(object):
    def setup_method(self):
        self.fake_binary = 'ceph'
        self.fake_cluster = 'ceph'
        self.fake_name = 'foo'
        self.fake_user = 'foo'
        self.fake_password = 'bar'
        self.fake_roles = ['read-only', 'block-manager']
        self.fake_params = {'cluster': self.fake_cluster,
                            'name': self.fake_user,
                            'password': self.fake_password,
                            'roles': self.fake_roles}
        self.fake_module = MagicMock()
        self.fake_module.params = self.fake_params

    def test_create_user(self):
        self.fake_module.params = self.fake_params
        expected_cmd = [
            self.fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-create',
            '-i', '-',
            self.fake_user
        ]

        assert ceph_dashboard_user.create_user(self.fake_module) == expected_cmd

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_create_user_container(self):
        fake_container_cmd = [
            fake_container_binary,
            'run',
            '--interactive',
            '--rm',
            '--net=host',
            '-v', '/etc/ceph:/etc/ceph:z',
            '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
            '-v', '/var/log/ceph/:/var/log/ceph/:z',
            '--entrypoint=' + self.fake_binary,
            fake_container_image
        ]
        self.fake_module.params = self.fake_params
        expected_cmd = fake_container_cmd + [
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-create',
            '-i', '-',
            self.fake_user
        ]

        assert ceph_dashboard_user.create_user(self.fake_module, container_image=fake_container_image) == expected_cmd

    def test_set_roles(self):
        self.fake_module.params = self.fake_params
        expected_cmd = [
            self.fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-set-roles',
            self.fake_user
        ]
        expected_cmd.extend(self.fake_roles)

        assert ceph_dashboard_user.set_roles(self.fake_module) == expected_cmd

    def test_set_password(self):
        self.fake_module.params = self.fake_params
        expected_cmd = [
            self.fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-set-password',
            '-i', '-',
            self.fake_user
        ]

        assert ceph_dashboard_user.set_password(self.fake_module) == expected_cmd

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_set_password_container(self):
        fake_container_cmd = [
            fake_container_binary,
            'run',
            '--interactive',
            '--rm',
            '--net=host',
            '-v', '/etc/ceph:/etc/ceph:z',
            '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
            '-v', '/var/log/ceph/:/var/log/ceph/:z',
            '--entrypoint=' + self.fake_binary,
            fake_container_image
        ]
        self.fake_module.params = self.fake_params
        expected_cmd = fake_container_cmd + [
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-set-password',
            '-i', '-',
            self.fake_user
        ]

        assert ceph_dashboard_user.set_password(self.fake_module, container_image=fake_container_image) == expected_cmd

    def test_get_user(self):
        self.fake_module.params = self.fake_params
        expected_cmd = [
            self.fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-show',
            self.fake_user,
            '--format=json'
        ]

        assert ceph_dashboard_user.get_user(self.fake_module) == expected_cmd

    def test_remove_user(self):
        self.fake_module.params = self.fake_params
        expected_cmd = [
            self.fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-delete',
            self.fake_user
        ]

        assert ceph_dashboard_user.remove_user(self.fake_module) == expected_cmd

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_create_user_fail_with_weak_password(self, m_run_command, m_fail_json):
        ca_test_common.set_module_args(self.fake_module.params)
        m_fail_json.side_effect = ca_test_common.fail_json
        get_rc = 2
        get_stderr = 'Error ENOENT: User {} does not exist.'.format(self.fake_user)
        get_stdout = ''
        create_rc = 22
        create_stderr = 'Error EINVAL: Password is too weak.'
        create_stdout = ''
        m_run_command.side_effect = [
            (get_rc, get_stdout, get_stderr),
            (create_rc, create_stdout, create_stderr)
        ]

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            ceph_dashboard_user.main()

        result = result.value.args[0]
        assert result['msg'] == create_stderr
        assert result['rc'] == 1
