import pytest


class TestOSDs(object):

    @pytest.mark.no_docker
    def test_ceph_osd_package_is_installed(self, node, host):
        assert host.package("ceph-osd").is_installed

    def test_osds_listen_on_public_network(self, node, host):
        # TODO: figure out way to paramaterize this test
        nb_port = (node["num_devices"] * 2)
        assert host.check_output("netstat -lntp | grep ceph-osd | grep %s | wc -l" % (node["address"])) == str(nb_port)

    def test_osds_listen_on_cluster_network(self, node, host):
        # TODO: figure out way to paramaterize this test
        nb_port = (node["num_devices"] * 2)
        assert host.check_output("netstat -lntp | grep ceph-osd | grep %s | wc -l" % (node["cluster_address"])) == str(nb_port)

    def test_osd_services_are_running(self, node, host):
        # TODO: figure out way to paramaterize node['osds'] for this test
        for osd in node["osds"]:
            assert host.service("ceph-osd@%s" % osd).is_running

    @pytest.mark.no_lvm_scenario
    def test_osd_services_are_enabled(self, node, host):
        # TODO: figure out way to paramaterize node['osds'] for this test
        for osd in node["osds"]:
            assert host.service("ceph-osd@%s" % osd).is_enabled

    @pytest.mark.no_docker
    def test_osd_are_mounted(self, node, host):
        # TODO: figure out way to paramaterize node['osd_ids'] for this test
        for osd_id in node["osd_ids"]:
            osd_path = "/var/lib/ceph/osd/{cluster}-{osd_id}".format(
                cluster=node["cluster_name"],
                osd_id=osd_id,
            )
            assert host.mount_point(osd_path).exists

    @pytest.mark.lvm_scenario
    def test_ceph_volume_is_installed(self, node, host):
        host.exists('ceph-volume')

    @pytest.mark.lvm_scenario
    def test_ceph_volume_systemd_is_installed(self, node, host):
        host.exists('ceph-volume-systemd')
