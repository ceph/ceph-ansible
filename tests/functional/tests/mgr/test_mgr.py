import pytest
import json

class TestMGRs(object):

    @pytest.mark.no_docker
    def test_mgr_is_installed(self, node, host):
        assert host.package("ceph-mgr").is_installed

    def test_mgr_service_is_running(self, node, host):
        service_name = "ceph-mgr@{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_running

    def test_mgr_service_is_enabled(self, node, host):
        service_name = "ceph-mgr@{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_enabled

    @pytest.mark.no_docker
    def test_mgr_is_up(self, node, host):
        hostname=node["vars"]["inventory_hostname"]
        cluster=node["cluster_name"]
        cmd = "sudo ceph --name mgr.{hostname} --keyring /var/lib/ceph/mgr/{cluster}-{hostname}/keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            hostname=hostname,
            cluster=cluster
        )
        output = host.check_output(cmd)
        daemons = json.loads(output)["mgrmap"]["active_name"]
        assert hostname in daemons

    @pytest.mark.docker
    def test_docker_mgr_is_up(self, node, host):
        hostname=node["vars"]["inventory_hostname"]
        cluster=node["cluster_name"]
        cmd = "sudo docker exec ceph-mgr-{hostname} ceph --name mgr.{hostname} --keyring /var/lib/ceph/mgr/{cluster}-{hostname}/keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            hostname=node["vars"]["inventory_hostname"],
            cluster=node["cluster_name"]
        )
        output_raw = host.check_output(cmd)
        output_json = json.loads(output_raw)
        daemons = output_json['mgrmap']['active_name']
        standbys = [i['name'] for i in output_json['mgrmap']['standbys']]
        result = hostname in daemons
        if not result:
            result = hostname in standbys
        assert result
