
class TestOSDs(object):

    def test_ceph_osd_package_is_installed(self, node, Package):
        assert Package("ceph-osd").is_installed

    def test_osd_listens_on_6800(self, node, Socket):
        assert Socket("tcp://%s:6800" % node["address"]).is_listening

    def test_osd_services_are_running(self, node, Service):
        # TODO: figure out way to paramaterize node['osd_ids'] for this test
        for osd_id in node["osd_ids"]:
            assert Service("ceph-osd@%s" % osd_id).is_running

    def test_osd_services_are_enabled(self, node, Service):
        # TODO: figure out way to paramaterize node['osd_ids'] for this test
        for osd_id in node["osd_ids"]:
            assert Service("ceph-osd@%s" % osd_id).is_enabled

    def test_osd_are_mounted(self, node, MountPoint):
        # TODO: figure out way to paramaterize node['osd_ids'] for this test
        for osd_id in node["osd_ids"]:
            osd_path = "/var/lib/ceph/osd/{cluster}-{osd_id}".format(
                cluster=node["cluster_name"],
                osd_id=osd_id,
            )
            assert MountPoint(osd_path).exists
