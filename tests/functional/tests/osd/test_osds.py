import pytest
import json
import os


class TestOSDs(object):

    @pytest.mark.no_docker
    def test_ceph_osd_package_is_installed(self, node, host):
        assert host.package("ceph-osd").is_installed

    def test_osds_listen_on_public_network(self, node, host):
        # TODO: figure out way to paramaterize this test
        nb_port = (node["num_osds"] * 2)
        assert host.check_output(
            "netstat -lntp | grep ceph-osd | grep %s | wc -l" % (node["address"])) == str(nb_port)  # noqa E501

    def test_osds_listen_on_cluster_network(self, node, host):
        # TODO: figure out way to paramaterize this test
        nb_port = (node["num_osds"] * 2)
        assert host.check_output("netstat -lntp | grep ceph-osd | grep %s | wc -l" %  # noqa E501
                                 (node["cluster_address"])) == str(nb_port)

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

    def _get_osd_id_from_host(self, node, osd_tree):
        children = []
        for n in osd_tree['nodes']:
            if n['name'] == node['vars']['inventory_hostname'] and n['type'] == 'host':  # noqa E501
                children = n['children']
        return children

    def _get_nb_up_osds_from_ids(self, node, osd_tree):
        nb_up = 0
        ids = self._get_osd_id_from_host(node, osd_tree)
        for n in osd_tree['nodes']:
            if n['id'] in ids and n['status'] == 'up':
                nb_up += 1
        return nb_up

    @pytest.mark.no_docker
    def test_all_osds_are_up_and_in(self, node, host):
        cmd = "sudo ceph --cluster={cluster} --connect-timeout 5 --keyring /var/lib/ceph/bootstrap-osd/{cluster}.keyring -n client.bootstrap-osd osd tree -f json".format(  # noqa E501
            cluster=node["cluster_name"])
        output = json.loads(host.check_output(cmd))
        assert node["num_osds"] == self._get_nb_up_osds_from_ids(node, output)

    @pytest.mark.docker
    def test_all_docker_osds_are_up_and_in(self, node, host):
        container_binary = 'docker'
        if host.exists('podman') and host.ansible("setup")["ansible_facts"]["ansible_distribution"] == 'Fedora':  # noqa E501
            container_binary = 'podman'
        osd_id = host.check_output(os.path.join(
            container_binary + " ps -q --filter='name=ceph-osd' | head -1"))
        cmd = "sudo {container_binary} exec {osd_id} ceph --cluster={cluster} --connect-timeout 5 --keyring /var/lib/ceph/bootstrap-osd/{cluster}.keyring -n client.bootstrap-osd osd tree -f json".format(  # noqa E501
            osd_id=osd_id,
            cluster=node["cluster_name"],
            container_binary=container_binary
        )
        output = json.loads(host.check_output(cmd))
        assert node["num_osds"] == self._get_nb_up_osds_from_ids(node, output)
