import os
import sys
from mock.mock import patch, MagicMock
import pytest
sys.path.append('./library')
import radosgw_account  # noqa: E402


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
fake_account_id = 'RGW00000000000000001'
fake_account_name = 'my-account'
fake_email = 'admin@example.com'
fake_realm = 'myrealm'
fake_zonegroup = 'myzonegroup'
fake_zone = 'myzone'
fake_params = {
    'cluster': fake_cluster,
    'account_id': fake_account_id,
    'account_name': fake_account_name,
    'email': fake_email,
    'realm': None,
    'zonegroup': None,
    'zone': None,
}


class TestRadosgwAccountModule(object):

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_container_exec(self):
        cmd = radosgw_account.container_exec(fake_binary, fake_container_image)
        assert cmd == fake_container_cmd

    def test_not_is_containerized(self):
        assert radosgw_account.is_containerized() is None

    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    def test_is_containerized(self):
        assert radosgw_account.is_containerized() == fake_container_image

    @pytest.mark.parametrize('image', [None, fake_container_image])
    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    def test_pre_generate_radosgw_cmd(self, image):
        if image:
            expected_cmd = fake_container_cmd
        else:
            expected_cmd = [fake_binary]

        assert radosgw_account.pre_generate_radosgw_cmd(image) == expected_cmd

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
            'account'
        ])
        assert radosgw_account.generate_radosgw_cmd(fake_cluster, [], image) == expected_cmd

    def test_get_account(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'account', 'get',
            '--account-id=' + fake_account_id,
            '--format=json'
        ]

        assert radosgw_account.get_account(fake_module) == expected_cmd

    def test_get_account_with_realm_zonegroup_zone(self):
        fake_module = MagicMock()
        fake_module.params = dict(fake_params,
                                  realm=fake_realm,
                                  zonegroup=fake_zonegroup,
                                  zone=fake_zone)
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'account', 'get',
            '--account-id=' + fake_account_id,
            '--format=json',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone
        ]

        assert radosgw_account.get_account(fake_module) == expected_cmd

    def test_create_account(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'account', 'create',
            '--account-id=' + fake_account_id,
            '--account-name=' + fake_account_name,
            '--email=' + fake_email
        ]

        assert radosgw_account.create_account(fake_module) == expected_cmd

    def test_create_account_minimal(self):
        fake_module = MagicMock()
        fake_module.params = dict(fake_params, account_name=None, email=None)
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'account', 'create',
            '--account-id=' + fake_account_id
        ]

        assert radosgw_account.create_account(fake_module) == expected_cmd

    def test_create_account_with_realm_zonegroup_zone(self):
        fake_module = MagicMock()
        fake_module.params = dict(fake_params,
                                  realm=fake_realm,
                                  zonegroup=fake_zonegroup,
                                  zone=fake_zone)
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'account', 'create',
            '--account-id=' + fake_account_id,
            '--account-name=' + fake_account_name,
            '--email=' + fake_email,
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone
        ]

        assert radosgw_account.create_account(fake_module) == expected_cmd

    def test_remove_account(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'account', 'rm',
            '--account-id=' + fake_account_id
        ]

        assert radosgw_account.remove_account(fake_module) == expected_cmd

    def test_remove_account_with_realm_zonegroup_zone(self):
        fake_module = MagicMock()
        fake_module.params = dict(fake_params,
                                  realm=fake_realm,
                                  zonegroup=fake_zonegroup,
                                  zone=fake_zone)
        expected_cmd = [
            fake_binary,
            '--cluster', fake_cluster,
            'account', 'rm',
            '--account-id=' + fake_account_id,
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone
        ]

        assert radosgw_account.remove_account(fake_module) == expected_cmd
