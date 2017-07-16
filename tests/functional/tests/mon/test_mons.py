import pytest


class TestMons(object):

    @pytest.mark.no_docker
    def test_ceph_mon_package_is_installed(self, node, Package):
        assert Package("ceph-mon").is_installed

    def test_mon_listens_on_6789(self, node, Socket):
        assert Socket("tcp://%s:6789" % node["address"]).is_listening

    def test_mon_service_is_running(self, node, Service):
        service_name = "ceph-mon@ceph-{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert Service(service_name).is_running

    def test_mon_service_is_enabled(self, node, Service):
        service_name = "ceph-mon@ceph-{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert Service(service_name).is_enabled

    @pytest.mark.no_docker
    def test_can_get_cluster_health(self, node, Command):
        cmd = "sudo ceph --cluster={} --connect-timeout 5 -s".format(node["cluster_name"])
        output = Command.check_output(cmd)
        assert output.strip().startswith("cluster")


class TestOSDs(object):

    @pytest.mark.no_docker
    def test_all_osds_are_up_and_in(self, node, Command):
        cmd = "sudo ceph --cluster={} --connect-timeout 5 -s".format(node["cluster_name"])
        output = Command.check_output(cmd)
        phrase = "{num_osds} osds: {num_osds} up, {num_osds} in".format(num_osds=node["total_osds"])
        assert phrase in output

    @pytest.mark.docker
    def test_all_docker_osds_are_up_and_in(self, node, Command):
        cmd = "sudo docker exec ceph-mon-ceph-{} ceph --cluster={} --connect-timeout 5 -s".format(
            node["vars"]["inventory_hostname"],
            node["cluster_name"]
        )
        output = Command.check_output(cmd)
        phrase = "{num_osds} osds: {num_osds} up, {num_osds} in".format(num_osds=node["total_osds"])
        assert phrase in output
