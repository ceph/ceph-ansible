import os
import sys
from mock.mock import patch, MagicMock
import pytest
sys.path.append('./library')
import ceph_fs  # noqa : E402


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
fake_fs = 'foo'
fake_data_pool = 'bar_data'
fake_metadata_pool = 'bar_metadata'
fake_max_mds = 2
fake_params = {'cluster': fake_cluster,
               'name': fake_fs,
               'data': fake_data_pool,
               'metadata': fake_metadata_pool,
               'max_mds': fake_max_mds}


class TestCephFsModule(object):

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_container_exec(self):
        cmd = ceph_fs.container_exec(fake_binary, fake_container_image)
        assert cmd == fake_container_cmd

    def test_not_is_containerized(self):
        assert ceph_fs.is_containerized() is None

    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_is_containerized(self):
        assert ceph_fs.is_containerized() == fake_container_image

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_pre_generate_ceph_cmd(self, image):
        if image:
            expected_cmd = fake_container_cmd
        else:
            expected_cmd = [fake_binary]

        assert ceph_fs.pre_generate_ceph_cmd(image) == expected_cmd

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
            'fs'
        ])
        assert ceph_fs.generate_ceph_cmd(fake_cluster, [], image) == expected_cmd

    def test_create_fs(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'fs', 'new',
            fake_fs,
            fake_metadata_pool,
            fake_data_pool
        ]

        assert ceph_fs.create_fs(fake_module) == expected_cmd

    def test_set_fs(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'fs', 'set',
            fake_fs,
            'max_mds',
            str(fake_max_mds)
        ]

        assert ceph_fs.set_fs(fake_module) == expected_cmd

    def test_get_fs(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'fs', 'get',
            fake_fs,
            '--format=json'
        ]

        assert ceph_fs.get_fs(fake_module) == expected_cmd

    def test_remove_fs(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'fs', 'rm',
            fake_fs,
            '--yes-i-really-mean-it'
        ]

        assert ceph_fs.remove_fs(fake_module) == expected_cmd

    def test_fail_fs(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'fs', 'fail',
            fake_fs
        ]

        assert ceph_fs.fail_fs(fake_module) == expected_cmd
