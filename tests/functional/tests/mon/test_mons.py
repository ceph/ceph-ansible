import pytest
import re

class TestMons(object):

    @pytest.mark.no_docker
    def test_ceph_mon_package_is_installed(self, node, host):
        assert host.package("ceph-mon").is_installed

    def test_mon_listens_on_6789(self, node, host):
        assert host.socket("tcp://%s:6789" % node["address"]).is_listening

    def test_mon_service_is_running(self, node, host):
        service_name = "ceph-mon@{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_running

    def test_mon_service_is_enabled(self, node, host):
        service_name = "ceph-mon@{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_enabled

    @pytest.mark.no_docker
    def test_can_get_cluster_health(self, node, host):
        cmd = "sudo ceph --cluster={} --connect-timeout 5 -s".format(node["cluster_name"])
        output = host.check_output(cmd)
        assert output.strip().startswith("cluster")

    def test_ceph_config_has_inital_members_line(self, node, host):
        assert host.file(node["conf_path"]).contains("^mon initial members = .*$")

    def test_initial_members_line_has_correct_value(self, node, host):
        mon_initial_members_line = host.check_output("grep 'mon initial members = ' /etc/ceph/{cluster}.conf".format(cluster=node['cluster_name']))
        result = True
        for host in node["vars"]["groups"]["mons"]:
            pattern = re.compile(host)
            if pattern.search(mon_initial_members_line) == None:
                result = False
                assert result

