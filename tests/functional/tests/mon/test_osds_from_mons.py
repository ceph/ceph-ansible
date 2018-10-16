import pytest
import json


class TestOsdsFromMons(object):
    def _get_nb_osd_up(self, osd_tree):
        nb_up = 0
        for n in osd_tree['nodes']:
            if n['type'] == 'osd' and n['status'] == 'up':
                nb_up += 1
        return nb_up

    @pytest.mark.no_docker
    def test_all_osds_are_up_and_in(self, node, host):
        cmd = "sudo ceph --cluster={cluster} --connect-timeout 5 osd tree -f json".format(cluster=node["cluster_name"])
        output = json.loads(host.check_output(cmd))
        nb_osd_up = self._get_nb_osd_up(output)
        assert int(node["num_osds"]) == int(nb_osd_up)

    @pytest.mark.docker
    def test_all_docker_osds_are_up_and_in(self, node, host):
        cmd = "sudo docker exec ceph-mon-{inventory_hostname} ceph --cluster={cluster} --connect-timeout 5 osd tree -f json".format(
            cluster=node["cluster_name"],
            inventory_hostname=node['vars']['inventory_hostname']
        )
        output = json.loads(host.check_output(cmd))
        nb_osd_up = self._get_nb_osd_up(output)
        assert node["num_osds"] == nb_osd_up
