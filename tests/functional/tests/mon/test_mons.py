
class TestMons(object):

    def test_mon_listens_on_6789(self, CephNode, Socket):
        assert Socket("tcp://%s:6789" % CephNode["address"]).is_listening

    def test_mon_service_is_running(self, CephNode, Service):
        service_name = "ceph-mon@ceph-%s" % CephNode["vars"]["inventory_hostname"]
        assert Service(service_name).is_running

    def test_mon_service_is_enabled(self, CephNode, Service):
        service_name = "ceph-mon@ceph-%s" % CephNode["vars"]["inventory_hostname"]
        assert Service(service_name).is_enabled

    def test_can_get_cluster_health(self, CephNode, Command):
        output = Command.check_output("sudo ceph -s")
        assert output.strip().startswith("cluster")


class TestOSDs(object):

    def test_all_osds_are_up_and_in(self, CephNode, Command):
        output = Command.check_output("sudo ceph -s")
        num_osds = len(CephNode["vars"]["devices"])
        phrase = "{num_osds} osds: {num_osds} up, {num_osds} in".format(num_osds=num_osds)
        assert phrase in output
