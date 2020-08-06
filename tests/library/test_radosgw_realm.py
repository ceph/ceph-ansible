import os
import sys
from mock.mock import patch, MagicMock
import pytest
sys.path.append('./library')
import radosgw_realm  # noqa: E402


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
fake_realm = 'foo'
fake_params = {'cluster': fake_cluster,
               'name': fake_realm,
               'default': True}


class TestRadosgwRealmModule(object):

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_container_exec(self):
        cmd = radosgw_realm.container_exec(fake_binary, fake_container_image)
        assert cmd == fake_container_cmd

    def test_not_is_containerized(self):
        assert radosgw_realm.is_containerized() is None

    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_is_containerized(self):
        assert radosgw_realm.is_containerized() == fake_container_image

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_pre_generate_radosgw_cmd(self, image):
        if image:
            expected_cmd = fake_container_cmd
        else:
            expected_cmd = [fake_binary]

        assert radosgw_realm.pre_generate_radosgw_cmd(image) == expected_cmd

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
            'realm'
        ])
        assert radosgw_realm.generate_radosgw_cmd(fake_cluster, [], image) == expected_cmd

    def test_create_realm(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'realm', 'create',
            '--rgw-realm=' + fake_realm,
            '--default'
        ]

        assert radosgw_realm.create_realm(fake_module) == expected_cmd

    def test_get_realm(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'realm', 'get',
            '--rgw-realm=' + fake_realm,
            '--format=json'
        ]

        assert radosgw_realm.get_realm(fake_module) == expected_cmd

    def test_remove_realm(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'realm', 'delete',
            '--rgw-realm=' + fake_realm
        ]

        assert radosgw_realm.remove_realm(fake_module) == expected_cmd
