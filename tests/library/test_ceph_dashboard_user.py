from mock.mock import MagicMock
import ceph_dashboard_user

fake_binary = 'ceph'
fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'docker.io/ceph/daemon:latest'
fake_container_cmd = [
    fake_container_binary,
    'run',
    '--rm',
    '--net=host',
    '-v', '/etc/ceph:/etc/ceph:z',
    '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
    '-v', '/var/log/ceph/:/var/log/ceph/:z',
    '--entrypoint=' + fake_binary,
    fake_container_image
]
fake_user = 'foo'
fake_password = 'bar'
fake_roles = ['read-only', 'block-manager']
fake_params = {'cluster': fake_cluster,
               'name': fake_user,
               'password': fake_password,
               'roles': fake_roles}


class TestCephDashboardUserModule(object):

    def test_create_user(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', fake_cluster,
            'dashboard', 'ac-user-create',
            fake_user,
            fake_password
        ]

        assert ceph_dashboard_user.create_user(fake_module) == expected_cmd

    def test_set_roles(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', fake_cluster,
            'dashboard', 'ac-user-set-roles',
            fake_user
        ]
        expected_cmd.extend(fake_roles)

        assert ceph_dashboard_user.set_roles(fake_module) == expected_cmd

    def test_set_password(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', fake_cluster,
            'dashboard', 'ac-user-set-password',
            fake_user,
            fake_password
        ]

        assert ceph_dashboard_user.set_password(fake_module) == expected_cmd

    def test_get_user(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', fake_cluster,
            'dashboard', 'ac-user-show',
            fake_user,
            '--format=json'
        ]

        assert ceph_dashboard_user.get_user(fake_module) == expected_cmd

    def test_remove_user(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', fake_cluster,
            'dashboard', 'ac-user-delete',
            fake_user
        ]

        assert ceph_dashboard_user.remove_user(fake_module) == expected_cmd
