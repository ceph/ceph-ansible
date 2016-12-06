
class TestInstall(object):

    def test_ceph_dir_exists(self, File):
        assert File('/etc/ceph').exists

    def test_ceph_dir_is_a_directory(self, File):
        assert File('/etc/ceph').is_directory

    def test_ceph_conf_exists(self, File):
        assert File('/etc/ceph/ceph.conf').exists

    def test_ceph_conf_is_a_file(self, File):
        assert File('/etc/ceph/ceph.conf').is_file

    def test_ceph_command_exists(self, Command):
        assert Command.exists("ceph")


class TestCephConf(object):

    def test_ceph_config_has_inital_members_line(self, node, File):
        assert File("/etc/ceph/ceph.conf").contains("^mon initial members = .*$")

    def test_initial_members_line_has_correct_value(self, node, File):
        mons = ",".join("ceph-%s" % host
                        for host in node["vars"]["groups"]["mons"])
        line = "mon initial members = {}".format(mons)
        assert File("/etc/ceph/ceph.conf").contains(line)

    def test_ceph_config_has_mon_host_line(self, node, File):
        assert File("/etc/ceph/ceph.conf").contains("^mon host = .*$")

    def test_mon_host_line_has_correct_value(self, node, File):
        mon_ips = []
        for x in range(0, node["num_mons"]):
            mon_ips.append("{}.1{}".format(node["subnet"], x))
        line = "mon host = {}".format(",".join(mon_ips))
        assert File("/etc/ceph/ceph.conf").contains(line)
