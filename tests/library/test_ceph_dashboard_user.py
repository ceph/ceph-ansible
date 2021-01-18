import os
from mock.mock import patch, MagicMock
import pytest
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

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_container_exec(self):
        fake_container_cmd = [
            fake_container_binary,
            'run',
            '--rm',
            '--net=host',
            '-v', '/etc/ceph:/etc/ceph:z',
            '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
            '-v', '/var/log/ceph/:/var/log/ceph/:z',
            '--entrypoint=' + self.fake_binary,
            fake_container_image
        ]
        cmd = ceph_dashboard_user.container_exec(self.fake_binary, fake_container_image)
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
            expected_cmd = [
                fake_container_binary,
                'run',
                '--rm',
                '--net=host',
                '-v', '/etc/ceph:/etc/ceph:z',
                '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v', '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=' + self.fake_binary,
                image
            ]
        else:
            expected_cmd = [self.fake_binary]

        assert ceph_dashboard_user.pre_generate_ceph_cmd(image) == expected_cmd

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_generate_ceph_cmd(self, image):
        if image:
            expected_cmd = [
                fake_container_binary,
                'run',
                '--rm',
                '--net=host',
                '-v', '/etc/ceph:/etc/ceph:z',
                '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v', '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=' + self.fake_binary,
                image
            ]
        else:
            expected_cmd = [self.fake_binary]

        expected_cmd.extend([
            '--cluster',
            self.fake_cluster,
            'dashboard'
        ])
        assert ceph_dashboard_user.generate_ceph_cmd(self.fake_cluster, [], image) == expected_cmd

    @pytest.mark.parametrize('interactive', [True, False])
    def test_create_user(self, interactive):
        self.fake_params.update({'interactive': interactive})
        self.fake_module.params = self.fake_params
        expected_cmd = [
            self.fake_binary,
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-create'
        ]
        if interactive:
            expected_cmd.extend([
                '-i', '-',
                self.fake_user
            ])
        else:
            expected_cmd.extend([
                self.fake_user,
                self.fake_password
            ])

        assert ceph_dashboard_user.create_user(self.fake_module) == expected_cmd

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    @pytest.mark.parametrize('interactive', [True, False])
    def test_create_user_container(self, interactive):
        self.fake_params.update({'interactive': interactive})
        self.fake_module.params = self.fake_params
        expected_cmd = [
            fake_container_binary,
            'run',
        ]
        if interactive:
            expected_cmd.append('--interactive')
        expected_cmd.extend([
            '--rm',
            '--net=host',
            '-v', '/etc/ceph:/etc/ceph:z',
            '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
            '-v', '/var/log/ceph/:/var/log/ceph/:z',
            '--entrypoint=' + self.fake_binary,
            fake_container_image,
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-create',
        ])
        if interactive:
            expected_cmd.extend([
                '-i', '-',
                self.fake_user
            ])
        else:
            expected_cmd.extend([
                self.fake_user,
                self.fake_password
            ])

        assert ceph_dashboard_user.create_user(self.fake_module, container_image=fake_container_image) == expected_cmd

    def test_set_roles(self):
        self.fake_module.params = self.fake_params
        expected_cmd = [
            self.fake_binary,
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-set-roles',
            self.fake_user
        ]
        expected_cmd.extend(self.fake_roles)

        assert ceph_dashboard_user.set_roles(self.fake_module) == expected_cmd

    @pytest.mark.parametrize('interactive', [True, False])
    def test_set_password(self, interactive):
        self.fake_params.update({'interactive': interactive})
        self.fake_module.params = self.fake_params
        expected_cmd = [
            self.fake_binary,
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-set-password',
        ]
        if interactive:
            expected_cmd.extend([
                '-i', '-',
                self.fake_user
            ])
        else:
            expected_cmd.extend([
                self.fake_user,
                self.fake_password
            ])

        assert ceph_dashboard_user.set_password(self.fake_module) == expected_cmd

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    @pytest.mark.parametrize('interactive', [True, False])
    def test_set_password_container(self, interactive):
        self.fake_params.update({'interactive': interactive})
        self.fake_module.params = self.fake_params
        expected_cmd = [
            fake_container_binary,
            'run',
        ]
        if interactive:
            expected_cmd.append('--interactive')
        expected_cmd.extend([
            '--rm',
            '--net=host',
            '-v', '/etc/ceph:/etc/ceph:z',
            '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
            '-v', '/var/log/ceph/:/var/log/ceph/:z',
            '--entrypoint=' + self.fake_binary,
            fake_container_image,
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-set-password',
        ])
        if interactive:
            expected_cmd.extend([
                '-i', '-',
                self.fake_user
            ])
        else:
            expected_cmd.extend([
                self.fake_user,
                self.fake_password
            ])

        assert ceph_dashboard_user.set_password(self.fake_module, container_image=fake_container_image) == expected_cmd

    def test_get_user(self):
        self.fake_module.params = self.fake_params
        expected_cmd = [
            self.fake_binary,
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
            '--cluster', self.fake_cluster,
            'dashboard', 'ac-user-delete',
            self.fake_user
        ]

        assert ceph_dashboard_user.remove_user(self.fake_module) == expected_cmd

    @pytest.mark.parametrize('stdin', [None, 'foo'])
    def test_exec_command(self, stdin):
        fake_module = MagicMock()
        rc = 0
        stderr = ''
        stdout = 'ceph version 1.2.3'
        fake_module.run_command.return_value = 0, stdout, stderr
        expected_cmd = [self.fake_binary, '--version']
        _rc, _cmd, _out, _err = ceph_dashboard_user.exec_commands(fake_module, expected_cmd, stdin=stdin)
        assert _rc == rc
        assert _cmd == expected_cmd
        assert _err == stderr
        assert _out == stdout
