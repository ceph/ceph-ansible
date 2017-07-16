import pytest


class TestInstall(object):

    def test_ceph_dir_exists(self, File, node):
        assert File('/etc/ceph').exists

    def test_ceph_dir_is_a_directory(self, File, node):
        assert File('/etc/ceph').is_directory

    def test_ceph_conf_exists(self, File, node):
        assert File(node["conf_path"]).exists

    def test_ceph_conf_is_a_file(self, File, node):
        assert File(node["conf_path"]).is_file

    @pytest.mark.no_docker
    def test_ceph_command_exists(self, Command, node):
        assert Command.exists("ceph")


class TestCephConf(object):

    def test_ceph_config_has_inital_members_line(self, node, File):
        assert File(node["conf_path"]).contains("^mon initial members = .*$")

    def test_initial_members_line_has_correct_value(self, node, File):
        mons = ",".join("ceph-%s" % host
                        for host in node["vars"]["groups"]["mons"])
        line = "mon initial members = {}".format(mons)
        assert File(node["conf_path"]).contains(line)

    def test_ceph_config_has_mon_host_line(self, node, File):
        assert File(node["conf_path"]).contains("^mon host = .*$")

    def test_mon_host_line_has_correct_value(self, node, File):
        mon_ips = []
        for x in range(0, node["num_mons"]):
            mon_ips.append("{}.1{}".format(node["subnet"], x))
        line = "mon host = {}".format(",".join(mon_ips))
        assert File(node["conf_path"]).contains(line)
