
class TestOSD(object):

    def test_osds_are_all_collocated(self, node, host):
        # TODO: figure out way to paramaterize node['vars']['devices'] for this test  # noqa E501
        osd_auto_discovery = node["vars"].get('osd_auto_discovery', False)
        if osd_auto_discovery:
            node["vars"]["devices"] = ["/dev/sda", "/dev/sdb", "/dev/sdc"]  # Hardcoded since we can't retrieve the devices list generated during playbook run  # noqa E501
        for device in node["vars"]["devices"]:
            assert host.check_output("sudo blkid -s PARTLABEL -o value $(readlink -f %s)2" % device) in ["ceph journal", "ceph block"]  # noqa E501
