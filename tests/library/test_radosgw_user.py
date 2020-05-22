import os
import sys
from mock.mock import patch, MagicMock
import pytest
sys.path.append('./library')
import radosgw_user  # noqa: E402


fake_binary = 'radosgw-admin'
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
fake_realm = 'canada'
fake_zonegroup = 'quebec'
fake_zone = 'montreal'
fake_params = {'cluster': fake_cluster,
               'name': fake_user,
               'display_name': fake_user,
               'email': fake_user,
               'access_key': 'PC7NPg87QWhOzXTkXIhX',
               'secret_key': 'jV64v39lVTjEx1ZJN6ocopnhvwMp1mXCD4kzBiPz',
               'realm': fake_realm,
               'zonegroup': fake_zonegroup,
               'zone': fake_zone,
               'system': True,
               'admin': True}


class TestRadosgwUserModule(object):

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_container_exec(self):
        cmd = radosgw_user.container_exec(fake_binary, fake_container_image)
        assert cmd == fake_container_cmd

    def test_not_is_containerized(self):
        assert radosgw_user.is_containerized() is None

    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_is_containerized(self):
        assert radosgw_user.is_containerized() == fake_container_image

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_pre_generate_radosgw_cmd(self, image):
        if image:
            expected_cmd = fake_container_cmd
        else:
            expected_cmd = [fake_binary]

        assert radosgw_user.pre_generate_radosgw_cmd(image) == expected_cmd

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_generate_radosgw_cmd(self, image):
        if image:
            expected_cmd = fake_container_cmd
        else:
            expected_cmd = [fake_binary]

        expected_cmd.extend([
            '--cluster',
            fake_cluster,
            'user'
        ])
        assert radosgw_user.generate_radosgw_cmd(fake_cluster, [], image) == expected_cmd

    def test_create_user(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'user', 'create',
            '--uid=' + fake_user,
            '--display_name=' + fake_user,
            '--email=' + fake_user,
            '--access-key=PC7NPg87QWhOzXTkXIhX',
            '--secret-key=jV64v39lVTjEx1ZJN6ocopnhvwMp1mXCD4kzBiPz',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone,
            '--system',
            '--admin'
        ]

        assert radosgw_user.create_user(fake_module) == expected_cmd

    def test_modify_user(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'user', 'modify',
            '--uid=' + fake_user,
            '--display_name=' + fake_user,
            '--email=' + fake_user,
            '--access-key=PC7NPg87QWhOzXTkXIhX',
            '--secret-key=jV64v39lVTjEx1ZJN6ocopnhvwMp1mXCD4kzBiPz',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone,
            '--system',
            '--admin'
        ]

        assert radosgw_user.modify_user(fake_module) == expected_cmd

    def test_get_user(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'user', 'info',
            '--uid=' + fake_user,
            '--format=json',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone
        ]

        assert radosgw_user.get_user(fake_module) == expected_cmd

    def test_remove_user(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'user', 'rm',
            '--uid=' + fake_user,
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone
        ]

        assert radosgw_user.remove_user(fake_module) == expected_cmd
