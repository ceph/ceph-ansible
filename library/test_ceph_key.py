import os
import pytest
from . import ceph_key


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
        expected_command_list = [
            'ceph',
            '--cluster',
            fake_cluster,
            'auth',
            'arg'
        ]
        result = ceph_key.generate_ceph_cmd(fake_cluster, fake_args)
        assert result == expected_command_list

    def test_generate_ceph_cmd_list_container(self):
        fake_cluster = "fake"
        fake_args = ['arg']
        fake_containerized = "docker exec -ti ceph-mon"
        expected_command_list = [
            'docker',
            'exec',
            '-ti',
            'ceph-mon',
            'ceph',
            '--cluster',
            fake_cluster,
            'auth',
            'arg'
        ]
        result = ceph_key.generate_ceph_cmd(
            fake_cluster, fake_args, fake_containerized)
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
        fake_file_destination = os.path.join(
            fake_dest + "/"+ fake_cluster + "." + fake_name + ".keyring")
        fake_auid = None
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
            fake_cluster, fake_name, fake_secret, fake_caps, fake_auid, fake_dest)
        assert result == expected_command_list

    def test_generate_ceph_authtool_cmd_non_container_auid(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_dest = "/fake/ceph"
        fake_file_destination = os.path.join(
            fake_dest + "/" + fake_cluster + "." + fake_name + ".keyring")
        fake_auid = 666
        expected_command_list = [
            'ceph-authtool',
            '--create-keyring',
            fake_file_destination,
            '--name',
            fake_name,
            '--add-key',
            fake_secret,
            '--set-uid',
            fake_auid,
            '--cap',
            'mon',
            'allow *',
            '--cap',
            'osd',
            'allow rwx',
        ]
        result = ceph_key.generate_ceph_authtool_cmd(
            fake_cluster, fake_name, fake_secret, fake_caps, fake_auid, fake_dest)
        assert result == expected_command_list

    def test_generate_ceph_authtool_cmd_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_containerized = "docker exec -ti ceph-mon"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_dest = "/fake/ceph"
        fake_auid = None
        fake_file_destination = os.path.join(
            fake_dest + "/" + fake_cluster + "." + fake_name + ".keyring")
        expected_command_list = [
            'docker',
            'exec',
            '-ti',
            'ceph-mon',
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
            'allow rwx'
        ]
        result = ceph_key.generate_ceph_authtool_cmd(
            fake_cluster, fake_name, fake_secret, fake_caps, fake_auid, fake_dest, fake_containerized)
        assert result == expected_command_list

    def test_create_key_non_container(self):
        fake_module = "fake"
        fake_result = "fake"
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_import_key = True
        fake_auid = None
        fake_dest = "/fake/ceph"
        fake_file_destination = os.path.join(
            fake_dest + "/" + fake_cluster + "." + fake_name + ".keyring")
        expected_command_list = [
            ['ceph-authtool', '--create-keyring', fake_file_destination, '--name', fake_name,
                '--add-key', fake_secret, '--cap', 'mon', 'allow *', '--cap', 'osd', 'allow rwx'],
            ['ceph', '--cluster', fake_cluster, 'auth',
                'import', '-i', fake_file_destination],
        ]
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster,
                                     fake_name, fake_secret, fake_caps, fake_import_key, fake_auid, fake_dest)
        assert result == expected_command_list

    def test_create_key_container(self):
        fake_module = "fake"
        fake_result = "fake"
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_containerized = "docker exec -ti ceph-mon"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_dest = "/fake/ceph"
        fake_import_key = True
        fake_auid = None
        fake_file_destination = os.path.join(
            fake_dest + "/" + fake_cluster + "." + fake_name + ".keyring")
        expected_command_list = [
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph-authtool', '--create-keyring', fake_file_destination,
                '--name', fake_name, '--add-key', fake_secret, '--cap', 'mon', 'allow *', '--cap', 'osd', 'allow rwx'],
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph', '--cluster',
                fake_cluster, 'auth', 'import', '-i', fake_file_destination],
        ]
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster, fake_name,
                                     fake_secret, fake_caps, fake_import_key, fake_auid, fake_dest, fake_containerized)
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
        fake_auid = None
        fake_file_destination = os.path.join(
            fake_dest + "/" + fake_cluster + "." + fake_name + ".keyring")
        # create_key passes (one for ceph-authtool and one for itself) itw own array so the expected result is an array within an array
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
                                     fake_name, fake_secret, fake_caps, fake_import_key, fake_auid, fake_dest)
        assert result == expected_command_list

    def test_create_key_container_no_import(self):
        fake_module = "fake"
        fake_result = "fake"
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_secret = "super-secret"
        fake_containerized = "docker exec -ti ceph-mon"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        fake_dest = "/fake/ceph"
        fake_import_key = False
        fake_file_destination = os.path.join(
            fake_dest + "/" + fake_cluster + "." + fake_name + ".keyring")
        fake_auid = None
        # create_key passes (one for ceph-authtool and one for itself) itw own array so the expected result is an array within an array
        expected_command_list = [[
            'docker',
            'exec',
            '-ti',
            'ceph-mon',
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
        result = ceph_key.create_key(fake_module, fake_result, fake_cluster, fake_name,
                                     fake_secret, fake_caps, fake_import_key, fake_auid, fake_dest, fake_containerized)
        assert result == expected_command_list

    def test_update_key_non_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        expected_command_list = [
            ['ceph', '--cluster', fake_cluster, 'auth', 'caps',
                fake_name, 'mon', 'allow *', 'osd', 'allow rwx'],
        ]
        result = ceph_key.update_key(fake_cluster, fake_name, fake_caps)
        assert result == expected_command_list

    def test_update_key_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_containerized = "docker exec -ti ceph-mon"
        fake_caps = {
            'mon': 'allow *',
            'osd': 'allow rwx',
        }
        expected_command_list = [
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph', '--cluster', fake_cluster,
                'auth', 'caps', fake_name, 'mon', 'allow *', 'osd', 'allow rwx'],
        ]
        result = ceph_key.update_key(
            fake_cluster, fake_name, fake_caps, fake_containerized)
        assert result == expected_command_list

    def test_delete_key_non_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        expected_command_list = [
            ['ceph', '--cluster', fake_cluster, 'auth', 'del', fake_name],
        ]
        result = ceph_key.delete_key(fake_cluster, fake_name)
        assert result == expected_command_list

    def test_delete_key_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_containerized = "docker exec -ti ceph-mon"
        expected_command_list = [
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph',
                '--cluster', fake_cluster, 'auth', 'del', fake_name],
        ]
        result = ceph_key.delete_key(
            fake_cluster, fake_name, fake_containerized)
        assert result == expected_command_list

    def test_info_key_non_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        expected_command_list = [
            ['ceph', '--cluster', fake_cluster, 'auth',
                'get', fake_name, '-f', 'json'],
        ]
        result = ceph_key.info_key(fake_cluster, fake_name)
        assert result == expected_command_list

    def test_info_key_container(self):
        fake_cluster = "fake"
        fake_name = "client.fake"
        fake_containerized = "docker exec -ti ceph-mon"
        expected_command_list = [
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph', '--cluster',
                fake_cluster, 'auth', 'get', fake_name, '-f', 'json'],
        ]
        result = ceph_key.info_key(fake_cluster, fake_name, fake_containerized)
        assert result == expected_command_list

    def test_list_key_non_container(self):
        fake_cluster = "fake"
        expected_command_list = [
            ['ceph', '--cluster', fake_cluster, 'auth', 'ls', '-f', 'json'],
        ]
        result = ceph_key.list_keys(fake_cluster)
        assert result == expected_command_list

    def test_list_key_container(self):
        fake_cluster = "fake"
        fake_containerized = "docker exec -ti ceph-mon"
        expected_command_list = [
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph', '--cluster',
                fake_cluster, 'auth', 'ls', '-f', 'json'],
        ]
        result = ceph_key.list_keys(fake_cluster, fake_containerized)
        assert result == expected_command_list
