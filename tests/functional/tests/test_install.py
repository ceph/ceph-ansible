import pytest
import re

class TestInstall(object):

    def test_ceph_dir_exists(self, host, node):
        assert host.file('/etc/ceph').exists

    def test_ceph_dir_is_a_directory(self, host, node):
        assert host.file('/etc/ceph').is_directory

    def test_ceph_conf_exists(self, host, node):
        assert host.file(node["conf_path"]).exists

    def test_ceph_conf_is_a_file(self, host, node):
        assert host.file(node["conf_path"]).is_file

    @pytest.mark.no_docker
    def test_ceph_command_exists(self, host, node):
        assert host.exists("ceph")


class TestCephConf(object):

    def test_ceph_config_has_mon_host_line(self, node, host):
        assert host.file(node["conf_path"]).contains("^mon host = .*$")

    def test_mon_host_line_has_correct_value(self, node, host):
        mon_host_line = host.check_output("grep 'mon host = ' /etc/ceph/{cluster}.conf".format(cluster=node['cluster_name']))
        result=True
        for x in range(0, node["num_mons"]):
            pattern=re.compile(("{}.1{}".format(node["subnet"], x)))
            if pattern.search(mon_host_line) == None:
                result=False
            assert result
