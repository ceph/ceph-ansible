from mock.mock import MagicMock
import radosgw_zone


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
fake_zone = 'z1'
fake_endpoints = ['http://192.168.1.10:8080', 'http://192.168.1.11:8080']
fake_params = {'cluster': fake_cluster,
               'name': fake_zone,
               'realm': fake_realm,
               'zonegroup': fake_zonegroup,
               'endpoints': fake_endpoints,
               'default': True,
               'master': True}
fake_admin = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_admin)


class TestRadosgwZoneModule(object):

    def test_create_zone(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', fake_admin, '-k', fake_keyring,
            '--cluster', fake_cluster,
            'zone', 'create',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone,
            '--endpoints=' + ','.join(fake_endpoints),
            '--default',
            '--master'
        ]

        assert radosgw_zone.create_zone(fake_module) == expected_cmd

    def test_modify_zone(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', fake_admin, '-k', fake_keyring,
            '--cluster', fake_cluster,
            'zone', 'modify',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone,
            '--endpoints=' + ','.join(fake_endpoints),
            '--default',
            '--master'
        ]

        assert radosgw_zone.modify_zone(fake_module) == expected_cmd

    def test_get_zone(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', fake_admin, '-k', fake_keyring,
            '--cluster', fake_cluster,
            'zone', 'get',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone,
            '--format=json'
        ]

        assert radosgw_zone.get_zone(fake_module) == expected_cmd

    def test_get_zonegroup(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', fake_admin, '-k', fake_keyring,
            '--cluster', fake_cluster,
            'zonegroup', 'get',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--format=json'
        ]

        assert radosgw_zone.get_zonegroup(fake_module) == expected_cmd

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

        assert radosgw_zone.get_realm(fake_module) == expected_cmd

    def test_remove_zone(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            '-n', fake_admin, '-k', fake_keyring,
            '--cluster', fake_cluster,
            'zone', 'delete',
            '--rgw-realm=' + fake_realm,
            '--rgw-zonegroup=' + fake_zonegroup,
            '--rgw-zone=' + fake_zone
        ]

        assert radosgw_zone.remove_zone(fake_module) == expected_cmd
