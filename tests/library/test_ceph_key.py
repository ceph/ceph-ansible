import json
import os
import sys
sys.path.append('./library')
import ceph_key
import mock


@mock.patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': 'docker'})
class TestCephKeyModule(object):

    def test_generate_secret(self):
        expected_length = 40
        result = len(ceph_key.generate_secret())
        assert result == expected_length

    def test_generate_caps_ceph_authtool(self):
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_cmd = ['ceph']
        fake_type = "ceph-authtool"
        expected_command_list = [
            'ceph',
            '--cap',
            'mon',
            'allow *',
            '--cap',
            'osd',
            'allow rwx'
        ]
        result = ceph_key.generate_caps(fake_cmd, fake_type, fake_caps)
        assert result == expected_command_list

    def test_generate_caps_not_ceph_authtool(self):
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_cmd = ['ceph']
        fake_type = ""
        expected_command_list = [
            'ceph',
            'mon',
            'allow *',
            'osd',
            'allow rwx'
        ]
        result = ceph_key.generate_caps(fake_cmd, fake_type, fake_caps)
        assert result == expected_command_list

    def test_generate_ceph_cmd_list_non_container(self):
        fake_cluster = "fake"
        fake_args = ['arg']
        fake_user = "fake-user"
        fake_key = "/tmp/my-key"
        expected_command_list = [
            'ceph',
            '-n',
            "fake-user",
            '-k',
            "/tmp/my-key",
            '--cluster',
            fake_cluster,
            'auth',
            'arg'
        ]
        result = ceph_key.generate_ceph_cmd(
            fake_cluster, fake_args, fake_user, fake_key)
        assert result == expected_command_list

    def test_generate_ceph_cmd_list_container(self):
        fake_cluster = "fake"
        fake_args = ['arg']
        fake_user = "fake-user"
        fake_key = "/tmp/my-key"
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = ['docker',
            'run',
            '--rm',
            '--net=host',  # noqa E501
            '-v', '/etc/ceph:/etc/ceph:z',
            '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
            '-v', '/var/log/ceph/:/var/log/ceph/:z',
            '--entrypoint=ceph',
            'docker.io/ceph/daemon:latest-luminous',
            '-n',
            "fake-user",
            '-k',
            "/tmp/my-key",
            '--cluster',
            fake_cluster,
            'auth',
            'arg']
        result = ceph_key.generate_ceph_cmd(
            fake_cluster, fake_args, fake_user, fake_key, fake_container_image)
        assert result == expected_command_list

    def test_generate_ceph_authtool_cmd_non_container_no_auid(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_dest = "/fake/ceph"
        fake_keyring_filename = fake_cluster + "." + fake_name + ".keyring"
        fake_file_destination = os.path.join(fake_dest, fake_keyring_filename)
        expected_command_list = [
            'ceph-authtool',
            '--create-keyring',
            fake_file_destination,
            '--name',
            fake_name,
            '--add-key',
            fake_secret,
            '--cap',
            'mon',
            'allow *',
            '--cap',
            'osd',
            'allow rwx',
        ]
        result = ceph_key.generate_ceph_authtool_cmd(
            fake_cluster, fake_name, fake_secret, fake_caps, fake_file_destination)  # noqa E501
        assert result == expected_command_list

    def test_generate_ceph_authtool_cmd_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_dest = "/fake/ceph"
        fake_keyring_filename = fake_cluster + "." + fake_name + ".keyring"
        fake_file_destination = os.path.join(fake_dest, fake_keyring_filename)
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = ['docker',
                                 'run',
                                 '--rm',
                                 '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph-authtool',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '--create-keyring',
                                 fake_file_destination,
                                 '--name',
                                 fake_name,
                                 '--add-key',
                                 fake_secret,
                                 '--cap',
                                 'mon',
                                 'allow *',
                                 '--cap',
                                 'osd',
                                 'allow rwx']
        result = ceph_key.generate_ceph_authtool_cmd(
            fake_cluster, fake_name, fake_secret, fake_caps, fake_file_destination, fake_container_image)  # noqa E501
        assert result == expected_command_list

    def test_create_key_non_container(self):
        fake_module = "fake"
        fake_result = " fake"
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_import_key = True
        fake_dest = "/fake/ceph"
        fake_keyring_filename = fake_cluster + "." + fake_name + ".keyring"
        fake_file_destination = os.path.join(fake_dest, fake_keyring_filename)
        expected_command_list = [
            ['ceph-authtool', '--create-keyring', fake_file_destination, '--name', fake_name,  # noqa E501
                '--add-key', fake_secret, '--cap', 'mon', 'allow *', '--cap', 'osd', 'allow rwx'],  # noqa E501
            ['ceph', '-n', 'client.admin', '-k', '/etc/ceph/fake.client.admin.keyring', '--cluster', fake_cluster, 'auth',  # noqa E501
                'import', '-i', fake_file_destination],
        ]
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster,
                                     fake_name, fake_secret, fake_caps, fake_import_key, fake_file_destination)  # noqa E501
        assert result == expected_command_list

    def test_create_key_container(self):
        fake_module = "fake"
        fake_result = "fake"
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_dest = "/fake/ceph"
        fake_import_key = True
        fake_keyring_filename = fake_cluster + "." + fake_name + ".keyring"
        fake_file_destination = os.path.join(fake_dest, fake_keyring_filename)
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = [
            ['docker',   # noqa E128
            'run',
            '--rm',
            '--net=host',
            '-v', '/etc/ceph:/etc/ceph:z',
            '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
            '-v', '/var/log/ceph/:/var/log/ceph/:z',
            '--entrypoint=ceph-authtool',
            'docker.io/ceph/daemon:latest-luminous',
            '--create-keyring', fake_file_destination,
            '--name', fake_name,
            '--add-key', fake_secret,
            '--cap', 'mon', 'allow *',
            '--cap', 'osd', 'allow rwx'],
            ['docker',
            'run',
            '--rm',
            '--net=host',
            '-v', '/etc/ceph:/etc/ceph:z',
            '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
            '-v', '/var/log/ceph/:/var/log/ceph/:z',
            '--entrypoint=ceph',
            'docker.io/ceph/daemon:latest-luminous',
            '-n', 'client.admin',
            '-k', '/etc/ceph/fake.client.admin.keyring',
            '--cluster', fake_cluster,
            'auth', 'import',
            '-i', fake_file_destination]
        ]
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster, fake_name,  # noqa E501
                                     fake_secret, fake_caps, fake_import_key, fake_file_destination, fake_container_image)  # noqa E501
        assert result == expected_command_list

    def test_create_key_non_container_no_import(self):
        fake_module = "fake"
        fake_result = "fake"
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_dest = "/fake/ceph"
        fake_import_key = False
        fake_keyring_filename = fake_cluster + "." + fake_name + ".keyring"
        fake_file_destination = os.path.join(fake_dest, fake_keyring_filename)
        # create_key passes (one for ceph-authtool and one for itself) itw own array so the expected result is an array within an array # noqa E501
        expected_command_list = [[
            'ceph-authtool',
            '--create-keyring',
            fake_file_destination,
            '--name',
            fake_name,
            '--add-key',
            fake_secret,
            '--cap',
            'mon',
            'allow *',
            '--cap',
            'osd',
            'allow rwx', ]
        ]
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster,
                                     fake_name, fake_secret, fake_caps, fake_import_key, fake_file_destination)  # noqa E501
        assert result == expected_command_list

    def test_create_key_container_no_import(self):
        fake_module = "fake"
        fake_result = "fake"
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_dest = "/fake/ceph"
        fake_import_key = False
        fake_keyring_filename = fake_cluster + "." + fake_name + ".keyring"
        fake_file_destination = os.path.join(fake_dest, fake_keyring_filename)
        # create_key passes (one for ceph-authtool and one for itself) itw own array so the expected result is an array within an array # noqa E501
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = [['docker',   # noqa E128
                                 'run',
                                 '--rm',
                                 '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph-authtool',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '--create-keyring',
                                 fake_file_destination,
                                 '--name',
                                 fake_name,
                                 '--add-key',
                                 fake_secret,
                                 '--cap',
                                 'mon',
                                 'allow *',
                                 '--cap',
                                 'osd',
                                 'allow rwx']]
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster, fake_name,  # noqa E501
                                     fake_secret, fake_caps, fake_import_key, fake_file_destination, fake_container_image)  # noqa E501
        assert result == expected_command_list

    def test_update_key_non_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        expected_command_list = [
            ['ceph', '-n', 'client.admin', '-k', '/etc/ceph/fake.client.admin.keyring',  '--cluster', fake_cluster, 'auth', 'caps',  # noqa E501
                fake_name, 'mon', 'allow *', 'osd', 'allow rwx'],
        ]
        result = ceph_key.update_key(fake_cluster, fake_name, fake_caps)
        assert result == expected_command_list

    def test_update_key_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = [['docker',   # noqa E128
                                 'run',
                                 '--rm',
                                 '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '-n', 'client.admin',
                                 '-k', '/etc/ceph/fake.client.admin.keyring',
                                 '--cluster', fake_cluster,
                                 'auth',
                                 'caps', fake_name,
                                 'mon', 'allow *', 'osd', 'allow rwx']
        ]
        result = ceph_key.update_key(
            fake_cluster, fake_name, fake_caps, fake_container_image)
        assert result == expected_command_list

    def test_delete_key_non_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        expected_command_list = [
            ['ceph',  '-n', 'client.admin', '-k', '/etc/ceph/fake.client.admin.keyring',  # noqa E501
                '--cluster', fake_cluster, 'auth', 'del', fake_name],
        ]
        result = ceph_key.delete_key(fake_cluster, fake_name)
        assert result == expected_command_list

    def test_delete_key_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = [['docker',   # noqa E128
                                 'run',
                                 '--rm',
                                 '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '-n', 'client.admin',
                                 '-k', '/etc/ceph/fake.client.admin.keyring',
                                 '--cluster', fake_cluster,
                                 'auth', 'del', fake_name]
        ]
        result = ceph_key.delete_key(
            fake_cluster, fake_name, fake_container_image)
        assert result == expected_command_list

    def test_info_key_non_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_user = "fake-user"
        fake_key = "/tmp/my-key"
        fake_output_format = "json"
        expected_command_list = [
            ['ceph', '-n', "fake-user", '-k', "/tmp/my-key", '--cluster', fake_cluster, 'auth',  # noqa E501
                'get', fake_name, '-f', 'json'],
        ]
        result = ceph_key.info_key(
            fake_cluster, fake_name, fake_user, fake_key, fake_output_format)
        assert result == expected_command_list

    def test_info_key_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_user = "fake-user"
        fake_key = "/tmp/my-key"
        fake_output_format = "json"
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = [['docker',   # noqa E128
                                 'run',
                                 '--rm',
                                 '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '-n', "fake-user",
                                 '-k', "/tmp/my-key",
                                 '--cluster', fake_cluster,
                                 'auth', 'get', fake_name,
                                 '-f', 'json']
        ]
        result = ceph_key.info_key(
            fake_cluster, fake_name, fake_user, fake_key, fake_output_format, fake_container_image)  # noqa E501
        assert result == expected_command_list

    def test_list_key_non_container(self):
        fake_cluster = "fake"
        fake_user = "fake-user"
        fake_key = "/tmp/my-key"
        expected_command_list = [
            ['ceph', '-n', "fake-user", '-k', "/tmp/my-key",
                '--cluster', fake_cluster, 'auth', 'ls', '-f', 'json'],
        ]
        result = ceph_key.list_keys(fake_cluster, fake_user, fake_key)
        assert result == expected_command_list

    def test_get_key_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        fake_dest = "/fake/ceph"
        fake_keyring_filename = fake_cluster + "." + fake_name + ".keyring"
        fake_file_destination = os.path.join(fake_dest, fake_keyring_filename)
        expected_command_list = [['docker',   # noqa E128
                                 'run',
                                 '--rm',
                                 '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '-n', "client.admin",
                                 '-k', "/etc/ceph/fake.client.admin.keyring",  # noqa E501
                                 '--cluster', fake_cluster,
                                 'auth', 'get',
                                 fake_name, '-o', fake_file_destination],
        ]
        result = ceph_key.get_key(
            fake_cluster, fake_name, fake_file_destination, fake_container_image)  # noqa E501
        assert result == expected_command_list

    def test_get_key_non_container(self):
        fake_cluster = "fake"
        fake_dest = "/fake/ceph"
        fake_name = "client.fake"
        fake_keyring_filename = fake_cluster + "." + fake_name + ".keyring"
        fake_file_destination = os.path.join(fake_dest, fake_keyring_filename)
        expected_command_list = [
            ['ceph', '-n', "client.admin", '-k', "/etc/ceph/fake.client.admin.keyring",  # noqa E501
                '--cluster', fake_cluster, 'auth', 'get', fake_name, '-o', fake_file_destination],  # noqa E501
        ]
        result = ceph_key.get_key(
            fake_cluster, fake_name, fake_file_destination)  # noqa E501
        assert result == expected_command_list

    def test_list_key_non_container_with_mon_key(self):
        fake_hostname = "mon01"
        fake_cluster = "fake"
        fake_user = "mon."
        fake_keyring_dirname = fake_cluster + "-" + fake_hostname
        fake_key = os.path.join("/var/lib/ceph/mon/", fake_keyring_dirname, 'keyring') # noqa E501
        expected_command_list = [
            ['ceph', '-n', "mon.", '-k', "/var/lib/ceph/mon/fake-mon01/keyring",  # noqa E501
                '--cluster', fake_cluster, 'auth', 'ls', '-f', 'json'],
        ]
        result = ceph_key.list_keys(fake_cluster, fake_user, fake_key)
        assert result == expected_command_list

    def test_list_key_container_with_mon_key(self):
        fake_hostname = "mon01"
        fake_cluster = "fake"
        fake_user = "mon."
        fake_keyring_dirname = fake_cluster + "-" + fake_hostname
        fake_key = os.path.join("/var/lib/ceph/mon/", fake_keyring_dirname, 'keyring') # noqa E501
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = [['docker',   # noqa E128
                                 'run',
                                 '--rm',
                                 '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '-n', "mon.",
                                 '-k', "/var/lib/ceph/mon/fake-mon01/keyring",  # noqa E501
                                 '--cluster', fake_cluster,
                                 'auth', 'ls',
                                 '-f', 'json'],
        ]
        result = ceph_key.list_keys(fake_cluster, fake_user, fake_key, fake_container_image)  # noqa E501
        assert result == expected_command_list

    def test_list_key_container(self):
        fake_cluster = "fake"
        fake_user = "fake-user"
        fake_key = "/tmp/my-key"
        fake_container_image = "docker.io/ceph/daemon:latest-luminous"
        expected_command_list = [['docker',   # noqa E128
                                 'run',
                                 '--rm',
                                 '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph',
                                 'docker.io/ceph/daemon:latest-luminous',
                                 '-n', "fake-user",
                                 '-k', "/tmp/my-key",
                                 '--cluster', fake_cluster,
                                 'auth', 'ls',
                                 '-f', 'json'],
        ]
        result = ceph_key.list_keys(
            fake_cluster, fake_user, fake_key, fake_container_image)
        assert result == expected_command_list

    def test_lookup_ceph_initial_entities(self):
        fake_module = "fake"
        fake_ceph_dict = { "auth_dump":[ { "entity":"osd.0", "key":"AQAJkMhbszeBBBAA4/V1tDFXGlft1GnHJS5wWg==", "caps":{ "mgr":"allow profile osd", "mon":"allow profile osd", "osd":"allow *" } }, { "entity":"osd.1", "key":"AQAjkMhbshueAhAAjZec50aBgd1NObLz57SQvg==", "caps":{ "mgr":"allow profile osd", "mon":"allow profile osd", "osd":"allow *" } }, { "entity":"client.admin", "key":"AQDZjshbrJv6EhAAY9v6LzLYNDpPdlC3HD5KHA==", "auid":0, "caps":{ "mds":"allow", "mgr":"allow *", "mon":"allow *", "osd":"allow *" } }, { "entity":"client.bootstrap-mds", "key":"AQDojshbc4QCHhAA1ZTrkt9dbSZRVU2GzI6U4A==", "caps":{ "mon":"allow profile bootstrap-mds" } }, { "entity":"client.bootstrap-mgr", "key":"AQBfiu5bAAAAABAARcNG24hUMlk4AdstVA5MVQ==", "caps":{ "mon":"allow profile bootstrap-mgr" } }, { "entity":"client.bootstrap-osd", "key":"AQDjjshbYW+uGxAAyHcPCXXmVoL8VsTBI8z1Ng==", "caps":{ "mon":"allow profile bootstrap-osd" } }, { "entity":"client.bootstrap-rbd", "key":"AQDyjshb522eIhAAtAz6nUPMOdG4H9u0NgpXhA==", "caps":{ "mon":"allow profile bootstrap-rbd" } }, { "entity":"client.bootstrap-rbd-mirror", "key":"AQDfh+5bAAAAABAAEGBD59Lj2vAKIdN8pq4lbQ==", "caps":{ "mon":"allow profile bootstrap-rbd-mirror" } }, { "entity":"client.bootstrap-rgw", "key":"AQDtjshbDl8oIBAAq1SfSYQKDR49hJNWJVwDQw==", "caps":{ "mon":"allow profile bootstrap-rgw" } }, { "entity":"mgr.mon0", "key":"AQA0j8hbgGapORAAoDkyAvXVkM5ej4wNn4cwTQ==", "caps":{ "mds":"allow *", "mon":"allow profile mgr", "osd":"allow *" } } ] }  # noqa E501
        fake_ceph_dict_str = json.dumps(fake_ceph_dict)  # convert to string
        expected_entity_list = ['client.admin', 'client.bootstrap-mds', 'client.bootstrap-mgr',  # noqa E501
                     'client.bootstrap-osd', 'client.bootstrap-rbd', 'client.bootstrap-rbd-mirror', 'client.bootstrap-rgw']  # noqa E501
        result = ceph_key.lookup_ceph_initial_entities(fake_module, fake_ceph_dict_str)
        assert result == expected_entity_list

    def test_build_key_path_admin(self):
        fake_cluster = "fake"
        entity = "client.admin"
        expected_result = "/etc/ceph/fake.client.admin.keyring"
        result = ceph_key.build_key_path(fake_cluster, entity)
        assert result == expected_result

    def test_build_key_path_bootstrap_osd(self):
        fake_cluster = "fake"
        entity = "client.bootstrap-osd"
        expected_result = "/var/lib/ceph/bootstrap-osd/fake.keyring"
        result = ceph_key.build_key_path(fake_cluster, entity)
        assert result == expected_result
