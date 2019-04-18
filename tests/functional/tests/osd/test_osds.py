import pytest
import json


class TestOSDs(object):

    @pytest.mark.no_docker
    def test_ceph_osd_package_is_installed(self, node, host):
        assert host.package("ceph-osd").is_installed

    def test_osds_listen_on_public_network(self, node, host, setup):
        # TODO: figure out way to paramaterize this test
        nb_port = (setup["num_osds"] * 4)
        assert host.check_output(
            "netstat -lntp | grep ceph-osd | grep %s | wc -l" % (setup["address"])) == str(nb_port)  # noqa E501

    def test_osds_listen_on_cluster_network(self, node, host, setup):
        # TODO: figure out way to paramaterize this test
        nb_port = (setup["num_osds"] * 4)
        assert host.check_output("netstat -lntp | grep ceph-osd | grep %s | wc -l" %  # noqa E501
                                 (setup["cluster_address"])) == str(nb_port)

    def test_osd_service_enabled_and_running(self, node, host, setup):
        # TODO: figure out way to paramaterize node['osds'] for this test
        for osd in setup["osds"]:
            s = host.service("ceph-osd@%s" % osd)
            assert s.is_enabled
            assert s.is_running

    @pytest.mark.no_docker
    def test_osd_are_mounted(self, node, host, setup):
        # TODO: figure out way to paramaterize setup['osd_ids'] for this test
        for osd_id in setup["osd_ids"]:
            osd_path = "/var/lib/ceph/osd/{cluster}-{osd_id}".format(
                cluster=setup["cluster_name"],
                osd_id=osd_id,
            )
            assert host.mount_point(osd_path).exists

    @pytest.mark.no_docker
    @pytest.mark.parametrize('cmd', [
        'ceph-volume',
        'ceph-volume-systemd'
    ])
    def test_ceph_volume_command_exists(self, node, host, cmd):
        assert host.exists(cmd)

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
    def test_all_osds_are_up_and_in(self, node, host, setup):
        cmd = "sudo ceph --cluster={cluster} --connect-timeout 5 --keyring /var/lib/ceph/bootstrap-osd/{cluster}.keyring -n client.bootstrap-osd osd tree -f json".format(  # noqa E501
            cluster=setup["cluster_name"])
        output = json.loads(host.check_output(cmd))
        assert setup["num_osds"] == self._get_nb_up_osds_from_ids(node, output)

    @pytest.mark.docker
    def test_all_docker_osds_are_up_and_in(self, node, host, setup):
        container_binary = setup["container_binary"]
        osd_id = host.check_output(container_binary + " ps -q --filter='name="
                                   "ceph-osd' | head -1")
        cmd = "sudo {container_binary} exec {osd_id} ceph --cluster={cluster} --connect-timeout 5 --keyring /var/lib/ceph/bootstrap-osd/{cluster}.keyring -n client.bootstrap-osd osd tree -f json".format(  # noqa E501
            osd_id=osd_id,
            cluster=setup["cluster_name"],
            container_binary=container_binary
        )
        output = json.loads(host.check_output(cmd))
        assert setup["num_osds"] == self._get_nb_up_osds_from_ids(node, output)
