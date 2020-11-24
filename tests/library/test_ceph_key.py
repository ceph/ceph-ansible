import json
import os
import sys
import mock
import pytest
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes

sys.path.append('./library')
import ceph_key  # noqa: E402


# From ceph-ansible documentation
def set_module_args(args):
    if '_ansible_remote_tmp' not in args:
        args['_ansible_remote_tmp'] = '/tmp'
    if '_ansible_keep_remote_files' not in args:
        args['_ansible_keep_remote_files'] = False

    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    raise AnsibleFailJson(kwargs)


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
        fake_type = "ceph-authtool"
        expected_command_list = [
            '--cap',
            'mon',
            'allow *',
            '--cap',
            'osd',
            'allow rwx'
        ]
        result = ceph_key.generate_caps(fake_type, fake_caps)
        assert result == expected_command_list

    def test_generate_caps_not_ceph_authtool(self):
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_type = ""
        expected_command_list = [
            'mon',
            'allow *',
            'osd',
            'allow rwx'
        ]
        result = ceph_key.generate_caps(fake_type, fake_caps)
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
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest-octopus"
        expected_command_list = ['docker',
                                 'run',
                                 '--rm',
                                 '--net=host',  # noqa E501
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph',
                                 'quay.ceph.io/ceph-ci/daemon:latest-octopus',
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
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest-octopus"
        expected_command_list = ['docker',
                                 'run',
                                 '--rm',
                                 '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph-authtool',
                                 'quay.ceph.io/ceph-ci/daemon:latest-octopus',
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
        fake_user = 'client.admin'
        fake_user_key = '/etc/ceph/fake.client.admin.keyring'
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
            ['ceph-authtool', '--create-keyring', fake_file_destination, '--name', fake_name,
                '--add-key', fake_secret, '--cap', 'mon', 'allow *', '--cap', 'osd', 'allow rwx'],
            ['ceph', '-n', fake_user, '-k', fake_user_key, '--cluster', fake_cluster, 'auth',
                'import', '-i', fake_file_destination],
        ]
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster, fake_user, fake_user_key,
                                     fake_name, fake_secret, fake_caps, fake_import_key, fake_file_destination)
        assert result == expected_command_list

    def test_create_key_container(self):
        fake_module = "fake"
        fake_user = 'client.admin'
        fake_user_key = '/etc/ceph/fake.client.admin.keyring'
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
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest-octopus"
        expected_command_list = [
            ['docker',
             'run',
             '--rm',
             '--net=host',
             '-v', '/etc/ceph:/etc/ceph:z',
             '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
             '-v', '/var/log/ceph/:/var/log/ceph/:z',
             '--entrypoint=ceph-authtool',
             'quay.ceph.io/ceph-ci/daemon:latest-octopus',
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
             'quay.ceph.io/ceph-ci/daemon:latest-octopus',
             '-n', 'client.admin',
             '-k', '/etc/ceph/fake.client.admin.keyring',
             '--cluster', fake_cluster,
             'auth', 'import',
             '-i', fake_file_destination]]
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster, fake_user, fake_user_key, fake_name,
                                     fake_secret, fake_caps, fake_import_key, fake_file_destination, fake_container_image)
        assert result == expected_command_list

    def test_create_key_non_container_no_import(self):
        fake_module = "fake"
        fake_user = 'client.admin'
        fake_user_key = '/etc/ceph/fake.client.admin.keyring'
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
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster, fake_user, fake_user_key,
                                     fake_name, fake_secret, fake_caps, fake_import_key, fake_file_destination)  # noqa E501
        assert result == expected_command_list

    def test_create_key_container_no_import(self):
        fake_module = "fake"
        fake_user = 'client.admin'
        fake_user_key = '/etc/ceph/fake.client.admin.keyring'
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
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest-octopus"
        expected_command_list = [['docker',
                                  'run',
                                  '--rm',
                                  '--net=host',
                                  '-v', '/etc/ceph:/etc/ceph:z',
                                  '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                  '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                  '--entrypoint=ceph-authtool',
                                  'quay.ceph.io/ceph-ci/daemon:latest-octopus',
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
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster, fake_user, fake_user_key, fake_name,
                                     fake_secret, fake_caps, fake_import_key, fake_file_destination, fake_container_image)
        assert result == expected_command_list

    def test_delete_key_non_container(self):
        fake_user = 'client.admin'
        fake_user_key = '/etc/ceph/fake.client.admin.keyring'
        fake_cluster = "fake"
        fake_name = "client.fake"
        expected_command_list = [
            ['ceph',  '-n', 'client.admin', '-k', '/etc/ceph/fake.client.admin.keyring',
                '--cluster', fake_cluster, 'auth', 'del', fake_name],
        ]
        result = ceph_key.delete_key(fake_cluster, fake_user, fake_user_key, fake_name)
        assert result == expected_command_list

    def test_delete_key_container(self):
        fake_user = 'client.admin'
        fake_user_key = '/etc/ceph/fake.client.admin.keyring'
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest-octopus"
        expected_command_list = [['docker',
                                  'run',
                                  '--rm',
                                  '--net=host',
                                  '-v', '/etc/ceph:/etc/ceph:z',
                                  '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                  '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                  '--entrypoint=ceph',
                                  'quay.ceph.io/ceph-ci/daemon:latest-octopus',
                                  '-n', 'client.admin',
                                  '-k', '/etc/ceph/fake.client.admin.keyring',
                                  '--cluster', fake_cluster,
                                  'auth', 'del', fake_name]]
        result = ceph_key.delete_key(
            fake_cluster, fake_user, fake_user_key, fake_name, fake_container_image)
        assert result == expected_command_list

    def test_info_key_non_container(self):
        fake_user = 'client.admin'
        fake_user_key = '/etc/ceph/fake.client.admin.keyring'
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_user = "fake-user"
        fake_output_format = "json"
        expected_command_list = [
            ['ceph', '-n', fake_user, '-k', fake_user_key, '--cluster', fake_cluster, 'auth',
                'get', fake_name, '-f', 'json'],
        ]
        result = ceph_key.info_key(
            fake_cluster, fake_name, fake_user, fake_user_key, fake_output_format)
        assert result == expected_command_list

    def test_info_key_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_user = 'client.admin'
        fake_user_key = '/etc/ceph/fake.client.admin.keyring'
        fake_output_format = "json"
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest-octopus"
        expected_command_list = [['docker',
                                  'run',
                                  '--rm',
                                  '--net=host',
                                  '-v', '/etc/ceph:/etc/ceph:z',
                                  '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                  '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                  '--entrypoint=ceph',
                                  'quay.ceph.io/ceph-ci/daemon:latest-octopus',
                                  '-n', fake_user,
                                  '-k', fake_user_key,
                                  '--cluster', fake_cluster,
                                  'auth', 'get', fake_name,
                                  '-f', 'json']]
        result = ceph_key.info_key(
            fake_cluster, fake_name, fake_user, fake_user_key, fake_output_format, fake_container_image)  # noqa E501
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
        fake_user = 'client.admin'
        fake_user_key = '/etc/ceph/fake.client.admin.keyring'
        fake_name = "client.fake"
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest-octopus"
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
                                  'quay.ceph.io/ceph-ci/daemon:latest-octopus',
                                  '-n', fake_user,
                                  '-k', fake_user_key,
                                  '--cluster', fake_cluster,
                                  'auth', 'get',
                                  fake_name, '-o', fake_file_destination]]
        result = ceph_key.get_key(
            fake_cluster, fake_user, fake_user_key, fake_name, fake_file_destination, fake_container_image)
        assert result == expected_command_list

    def test_get_key_non_container(self):
        fake_cluster = "fake"
        fake_user = 'client.admin'
        fake_user_key = '/etc/ceph/fake.client.admin.keyring'
        fake_dest = "/fake/ceph"
        fake_name = "client.fake"
        fake_keyring_filename = fake_cluster + "." + fake_name + ".keyring"
        fake_file_destination = os.path.join(fake_dest, fake_keyring_filename)
        expected_command_list = [
            ['ceph', '-n', fake_user, '-k', fake_user_key,
                '--cluster', fake_cluster, 'auth', 'get', fake_name, '-o', fake_file_destination],
        ]
        result = ceph_key.get_key(
            fake_cluster, fake_user, fake_user_key, fake_name, fake_file_destination)
        assert result == expected_command_list

    def test_list_key_non_container_with_mon_key(self):
        fake_hostname = "mon01"
        fake_cluster = "fake"
        fake_user = "mon."
        fake_keyring_dirname = fake_cluster + "-" + fake_hostname
        fake_key = os.path.join("/var/lib/ceph/mon/", fake_keyring_dirname, 'keyring')
        expected_command_list = [
            ['ceph', '-n', "mon.", '-k', "/var/lib/ceph/mon/fake-mon01/keyring",
                '--cluster', fake_cluster, 'auth', 'ls', '-f', 'json'],
        ]
        result = ceph_key.list_keys(fake_cluster, fake_user, fake_key)
        assert result == expected_command_list

    def test_list_key_container_with_mon_key(self):
        fake_hostname = "mon01"
        fake_cluster = "fake"
        fake_user = "mon."
        fake_keyring_dirname = fake_cluster + "-" + fake_hostname
        fake_key = os.path.join("/var/lib/ceph/mon/", fake_keyring_dirname, 'keyring')
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest-octopus"
        expected_command_list = [['docker',
                                  'run',
                                  '--rm',
                                  '--net=host',
                                  '-v', '/etc/ceph:/etc/ceph:z',
                                  '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                  '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                  '--entrypoint=ceph',
                                  'quay.ceph.io/ceph-ci/daemon:latest-octopus',
                                  '-n', "mon.",
                                  '-k', "/var/lib/ceph/mon/fake-mon01/keyring",
                                  '--cluster', fake_cluster,
                                  'auth', 'ls',
                                  '-f', 'json'], ]
        result = ceph_key.list_keys(fake_cluster, fake_user, fake_key, fake_container_image)
        assert result == expected_command_list

    def test_list_key_container(self):
        fake_cluster = "fake"
        fake_user = "fake-user"
        fake_key = "/tmp/my-key"
        fake_container_image = "quay.ceph.io/ceph-ci/daemon:latest-octopus"
        expected_command_list = [['docker',
                                  'run',
                                  '--rm',
                                  '--net=host',
                                  '-v', '/etc/ceph:/etc/ceph:z',
                                  '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                  '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                  '--entrypoint=ceph',
                                  'quay.ceph.io/ceph-ci/daemon:latest-octopus',
                                  '-n', "fake-user",
                                  '-k', "/tmp/my-key",
                                  '--cluster', fake_cluster,
                                  'auth', 'ls',
                                  '-f', 'json'], ]
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

    @mock.patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @mock.patch('ceph_key.exec_commands')
    def test_state_info(self, m_exec_commands, m_exit_json):
        set_module_args({"state": "info",
                         "cluster": "ceph",
                         "name": "client.admin"}
                        )
        m_exit_json.side_effect = exit_json
        m_exec_commands.return_value = (0,
                                        ['ceph', 'auth', 'get', 'client.admin', '-f', 'json'],
                                        '[{"entity":"client.admin","key":"AQC1tw5fF156GhAAoJCvHGX/jl/k7/N4VZm8iQ==","caps":{"mds":"allow *","mgr":"allow *","mon":"allow *","osd":"allow *"}}]',  # noqa: E501
                                        'exported keyring for client.admin')

        with pytest.raises(AnsibleExitJson) as result:
            ceph_key.run_module()

        result = result.value.args[0]
        assert not result['changed']
        assert result['stdout'] == '[{"entity":"client.admin","key":"AQC1tw5fF156GhAAoJCvHGX/jl/k7/N4VZm8iQ==","caps":{"mds":"allow *","mgr":"allow *","mon":"allow *","osd":"allow *"}}]'  # noqa: E501
        assert result['stderr'] == 'exported keyring for client.admin'
        assert result['rc'] == 0

    @mock.patch('ceph_key.generate_secret')
    @mock.patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_generate_key(self, m_exit_json, m_generate_secret):
        fake_secret = b'AQDaLb1fAAAAABAAsIMKdGEKu+lGOyXnRfT0Hg=='
        set_module_args({"state": "generate_secret"})
        m_exit_json.side_effect = exit_json
        m_generate_secret.return_value = fake_secret

        with pytest.raises(AnsibleExitJson) as result:
            ceph_key.run_module()
        assert result.value.args[0]['stdout'] == fake_secret.decode()
