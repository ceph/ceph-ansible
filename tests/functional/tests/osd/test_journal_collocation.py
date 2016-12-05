
class TestOSD(object):

    def test_osds_are_all_collocated(self, CephNode, Command):
        # TODO: figure out way to paramaterize CephNode['vars']['devices'] for this test
        for device in CephNode["vars"]["devices"]:
            assert Command.check_output("sudo blkid -s PARTLABEL -o value %s2" % device) == "ceph journal"
