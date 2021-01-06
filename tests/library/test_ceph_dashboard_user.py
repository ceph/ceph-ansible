from mock.mock import MagicMock, patch
import os
import ceph_dashboard_user

fake_container_binary = 'podman'
fake_container_image = 'docker.io/ceph/daemon:latest'


class TestCephDashboardUserModule(object):
    def setup_method(self):
        self.fake_params = []
        self.fake_binary = 'ceph'
        self.fake_cluster = 'ceph'
        self.fake_name = 'foo'
        self.fake_user = 'foo'
        self.fake_password = 'bar'
        self.fake_module = MagicMock()
        self.fake_module.params = self.fake_params
        self.fake_roles = ['read-only', 'block-manager']
        self.fake_params = {'cluster': self.fake_cluster,
                            'name': self.fake_user,
                            'password': self.fake_password,
                            'roles': self.fake_roles}

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
