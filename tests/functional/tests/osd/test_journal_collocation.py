
class TestOSD(object):

    def test_osds_are_all_collocated(self, node, Command):
        # TODO: figure out way to paramaterize node['vars']['devices'] for this test
        for device in node["vars"]["devices"]:
            assert Command.check_output("sudo blkid -s PARTLABEL -o value %s2" % device) in ["ceph journal", "ceph block"]
