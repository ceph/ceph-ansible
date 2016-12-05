
class TestOSDs(object):

    def test_ceph_osd_package_is_installed(self, CephNode, Package):
        assert Package("ceph-osd").is_installed

    def test_osd_listens_on_6800(self, CephNode, Socket):
        assert Socket("tcp://%s:6800" % CephNode["address"]).is_listening

    def test_osd_services_are_running(self, CephNode, Service):
        # TODO: figure out way to paramaterize CephNode['osd_ids'] for this test
        for osd_id in CephNode["osd_ids"]:
            assert Service("ceph-osd@%s" % osd_id).is_running

    def test_osd_services_are_enabled(self, CephNode, Service):
        # TODO: figure out way to paramaterize CephNode['osd_ids'] for this test
        for osd_id in CephNode["osd_ids"]:
            assert Service("ceph-osd@%s" % osd_id).is_enabled

    def test_osd_are_mounted(self, CephNode, MountPoint):
        # TODO: figure out way to paramaterize CephNode['osd_ids'] for this test
        for osd_id in CephNode["osd_ids"]:
            assert MountPoint("/var/lib/ceph/osd/ceph-%s" % osd_id).exists
