import os
import sys
from mock.mock import patch, MagicMock
import pytest
sys.path.append('./library')
import radosgw_zonegroup  # noqa: E402


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
fake_zonegroup = 'bar'
fake_endpoints = ['http://192.168.1.10:8080', 'http://192.168.1.11:8080']
fake_params = {'cluster': fake_cluster,
               'name': fake_zonegroup,
               'realm': fake_realm,
               'endpoints': fake_endpoints,
               'default': True,
               'master': True}


class TestRadosgwZonegroupModule(object):

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_container_exec(self):
        cmd = radosgw_zonegroup.container_exec(fake_binary, fake_container_image)
        assert cmd == fake_container_cmd

    def test_not_is_containerized(self):
        assert radosgw_zonegroup.is_containerized() is None

    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_is_containerized(self):
        assert radosgw_zonegroup.is_containerized() == fake_container_image

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_pre_generate_radosgw_cmd(self, image):
        if image:
            expected_cmd = fake_container_cmd
        else:
            expected_cmd = [fake_binary]

        assert radosgw_zonegroup.pre_generate_radosgw_cmd(image) == expected_cmd

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
            'zonegroup'
        ])
        assert radosgw_zonegroup.generate_radosgw_cmd(fake_cluster, [], image) == expected_cmd

    def test_create_zonegroup(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'zonegroup', 'create',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--endpoints=' + ','.join(fake_endpoints),
            '--default',
            '--master'
        ]

        assert radosgw_zonegroup.create_zonegroup(fake_module) == expected_cmd

    def test_modify_zonegroup(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'zonegroup', 'modify',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--endpoints=' + ','.join(fake_endpoints),
            '--default',
            '--master'
        ]

        assert radosgw_zonegroup.modify_zonegroup(fake_module) == expected_cmd

    def test_get_zonegroup(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'zonegroup', 'get',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--format=json'
        ]

        assert radosgw_zonegroup.get_zonegroup(fake_module) == expected_cmd

    def test_remove_zonegroup(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'zonegroup', 'delete',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup
        ]

        assert radosgw_zonegroup.remove_zonegroup(fake_module) == expected_cmd
