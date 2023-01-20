import pytest
import json


class TestMDSs(object):

    @pytest.mark.no_docker
    def test_mds_is_installed(self, node, host):
        assert host.package("ceph-mds").is_installed

    def test_mds_service_enabled_and_running(self, node, host):
        service_name = "ceph-mds@{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        s = host.service(service_name)
        assert s.is_enabled
        assert s.is_running

    def test_mds_is_up(self, node, setup, ceph_status):
        cluster = setup["cluster_name"]
        name = 'client.bootstrap-mds'
        output = ceph_status(f'/var/lib/ceph/bootstrap-mds/{cluster}.keyring', name=name)
        cluster_status = json.loads(output)
        assert (cluster_status['fsmap'].get('up', 0) + cluster_status['fsmap'].get(  # noqa E501
            'up:standby', 0)) == len(node["vars"]["groups"]["mdss"])
