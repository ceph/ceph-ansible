import pytest


class TestOSDs(object):

    @pytest.mark.no_docker
    def test_ceph_osd_package_is_installed(self, node, Package):
        assert Package("ceph-osd").is_installed

    def test_osds_listen_on_public_network(self, node, Socket):
        # TODO: figure out way to paramaterize this test
        for x in range(0, node["num_devices"] * 2):
            port = "680{}".format(x)
            assert Socket("tcp://{address}:{port}".format(
                address=node["address"],
                port=port,
            )).is_listening

    def test_osds_listen_on_cluster_network(self, node, Socket):
        # TODO: figure out way to paramaterize this test
        for x in range(0, node["num_devices"] * 2):
            port = "680{}".format(x)
            assert Socket("tcp://{address}:{port}".format(
                address=node["cluster_address"],
                port=port,
            )).is_listening

    def test_osd_services_are_running(self, node, Service):
        # TODO: figure out way to paramaterize node['osd_ids'] for this test
        for osd_id in node["osd_ids"]:
            assert Service("ceph-osd@%s" % osd_id).is_running

    def test_osd_services_are_enabled(self, node, Service):
        # TODO: figure out way to paramaterize node['osd_ids'] for this test
        for osd_id in node["osd_ids"]:
            assert Service("ceph-osd@%s" % osd_id).is_enabled

    @pytest.mark.no_docker
    def test_osd_are_mounted(self, node, MountPoint):
        # TODO: figure out way to paramaterize node['osd_ids'] for this test
        for osd_id in node["osd_ids"]:
            osd_path = "/var/lib/ceph/osd/{cluster}-{osd_id}".format(
                cluster=node["cluster_name"],
                osd_id=osd_id,
            )
            assert MountPoint(osd_path).exists
