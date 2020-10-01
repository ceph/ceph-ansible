import os
import sys
from mock.mock import patch, MagicMock
import pytest
sys.path.append('./library')
import ceph_dashboard_user  # noqa: E402

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

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_container_exec(self):
        cmd = ceph_dashboard_user.container_exec(fake_binary, fake_container_image)
        assert cmd == fake_container_cmd

    def test_not_is_containerized(self):
        assert ceph_dashboard_user.is_containerized() is None

    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_is_containerized(self):
        assert ceph_dashboard_user.is_containerized() == fake_container_image

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_pre_generate_ceph_cmd(self, image):
        if image:
            expected_cmd = fake_container_cmd
        else:
            expected_cmd = [fake_binary]

        assert ceph_dashboard_user.pre_generate_ceph_cmd(image) == expected_cmd

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_generate_ceph_cmd(self, image):
        if image:
            expected_cmd = fake_container_cmd
        else:
            expected_cmd = [fake_binary]

        expected_cmd.extend([
            '--cluster',
            fake_cluster,
            'dashboard'
        ])
        assert ceph_dashboard_user.generate_ceph_cmd(fake_cluster, [], image) == expected_cmd

    def test_create_user(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
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
            '--cluster', fake_cluster,
            'dashboard', 'ac-user-delete',
            fake_user
        ]

        assert ceph_dashboard_user.remove_user(fake_module) == expected_cmd
