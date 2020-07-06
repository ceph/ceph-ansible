import pytest
import json
import os


class TestOSDs(object):

    def _get_osds_id(self, node, host):
        osds = []
        cmd = host.run('sudo ls /var/lib/ceph/osd/ | sed "s/.*-//"')
        if cmd.rc == 0:
            osds = cmd.stdout.rstrip("\n").split("\n")
        return osds

    def _get_docker_exec_cmd(self, node, host):
        osd_id = host.check_output(
            "{container_binary} ps -q --filter='name=ceph-osd' | head -1".format(container_binary=node['container_binary']))
        return osd_id


    @pytest.mark.no_docker
    def test_ceph_osd_package_is_installed(self, node, host):
        assert host.package("ceph-osd").is_installed

    def test_osds_listen_on_public_network(self, node, host):
        # TODO: figure out way to paramaterize this test
        nb_port = (node["num_osds"] * 2)
        assert host.check_output("netstat -lntp | grep ceph-osd | grep %s | wc -l" % (node["address"])) == str(nb_port)

    def test_osds_listen_on_cluster_network(self, node, host):
        # TODO: figure out way to paramaterize this test
        nb_port = (node["num_osds"] * 2)
        assert host.check_output("netstat -lntp | grep ceph-osd | grep %s | wc -l" % (host.interface("eth2").addresses[0])) == str(nb_port)

    def test_osd_services_are_running(self, node, host):
        # TODO: figure out way to paramaterize node['osds'] for this test
#        for osd in node["osds"]:
        for osd in self._get_osds_id(node, host):
            assert host.service("ceph-osd@%s" % osd).is_running

    @pytest.mark.no_lvm_scenario
    def test_osd_services_are_enabled(self, node, host):
        # TODO: figure out way to paramaterize node['osds'] for this test
#        for osd in node["osds"]:
        for osd in self._get_osds_id(node, host):
            assert host.service("ceph-osd@%s" % osd).is_enabled

    @pytest.mark.no_docker
    def test_osd_are_mounted(self, node, host):
        # TODO: figure out way to paramaterize node['osd_ids'] for this test
        for osd_id in self._get_osds_id(node, host):
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
            if n['name'] == node['vars']['inventory_hostname'] and n['type'] == 'host':
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
        cmd = "sudo ceph --cluster={cluster} --connect-timeout 5 --keyring /var/lib/ceph/bootstrap-osd/{cluster}.keyring -n client.bootstrap-osd osd tree -f json".format(cluster=node["cluster_name"])
        output = json.loads(host.check_output(cmd))
        assert node["num_osds"] == self._get_nb_up_osds_from_ids(node, output)

    @pytest.mark.docker
    def test_all_docker_osds_are_up_and_in(self, node, host):
        container_binary= node['container_binary']
        cmd = "sudo {container_binary} exec {osd_id} ceph --cluster={cluster} --connect-timeout 5 --keyring /var/lib/ceph/bootstrap-osd/{cluster}.keyring -n client.bootstrap-osd osd tree -f json".format(
            container_binary=container_binary,
            osd_id=self._get_docker_exec_cmd(node, host),
            cluster=node["cluster_name"]
        )
        output = json.loads(host.check_output(cmd))
        assert node["num_osds"] == self._get_nb_up_osds_from_ids(node, output)