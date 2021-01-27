from mock.mock import MagicMock
import radosgw_user


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
fake_admin = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_admin)


class TestRadosgwUserModule(object):

    def test_create_user(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', fake_admin, '-k', fake_keyring,
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
            '-n', fake_admin, '-k', fake_keyring,
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
            '-n', fake_admin, '-k', fake_keyring,
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
            '-n', fake_admin, '-k', fake_keyring,
            '--cluster', fake_cluster,
            'user', 'rm',
            '--uid=' + fake_user,
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone
        ]

        assert radosgw_user.remove_user(fake_module) == expected_cmd
