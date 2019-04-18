import pytest
import re


class TestInstall(object):

    def test_ceph_dir_exists_and_is_directory(self, host, node):
        f = host.file('/etc/ceph')
        assert f.exists
        assert f.is_directory

    def test_ceph_conf_exists_and_is_file(self, host, node, setup):
        f = host.file(setup["conf_path"])
        assert f.exists
        assert f.is_file

    @pytest.mark.no_docker
    def test_ceph_command_exists(self, host, node):
        assert host.exists("ceph")


class TestCephConf(object):

    def test_mon_host_line_has_correct_value(self, node, host, setup):
        mon_host_line = host.check_output("grep 'mon host = ' /etc/ceph/{cluster}.conf".format(cluster=setup['cluster_name']))  # noqa E501
        result = True
        for x in range(0, setup["num_mons"]):
            pattern = re.compile(("v2:{subnet}.1{x}:3300,v1:{subnet}.1{x}:6789".format(subnet=setup["subnet"], x=x)))  # noqa E501
            if pattern.search(mon_host_line) is None:
                result = False
            assert result
