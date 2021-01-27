from mock.mock import MagicMock
import radosgw_realm


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
fake_admin = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_admin)


class TestRadosgwRealmModule(object):

    def test_create_realm(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', fake_admin, '-k', fake_keyring,
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
            '-n', fake_admin, '-k', fake_keyring,
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
            '-n', fake_admin, '-k', fake_keyring,
            '--cluster', fake_cluster,
            'realm', 'delete',
            '--rgw-realm=' + fake_realm
        ]

        assert radosgw_realm.remove_realm(fake_module) == expected_cmd
