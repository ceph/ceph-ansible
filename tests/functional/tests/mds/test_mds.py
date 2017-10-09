import pytest
import json

class TestMDSs(object):

    @pytest.mark.no_docker
    def test_mds_is_installed(self, node, host):
        assert host.package("ceph-mds").is_installed

    def test_mds_service_is_running(self, node, host):
        service_name = "ceph-mds@{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_running

    def test_mds_service_is_enabled(self, node, host):
        service_name = "ceph-mds@{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_enabled

    @pytest.mark.no_docker
    def test_mds_is_up(self, node, host):
        hostname = node["vars"]["inventory_hostname"]
        cmd = "sudo ceph --name client.bootstrap-mds --keyring /var/lib/ceph/bootstrap-mds/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(cluster=node['cluster_name'])
        output = host.check_output(cmd)
        daemons = json.loads(output)["fsmap"]["by_rank"][0]["name"]
        assert hostname in daemons

    @pytest.mark.docker
    def test_docker_mds_is_up(self, node, host):
        hostname = node["vars"]["inventory_hostname"]
        cmd = "sudo docker exec ceph-mds-{hostname} ceph --name client.bootstrap-mds --keyring /var/lib/ceph/bootstrap-mds/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            hostname=node["vars"]["inventory_hostname"],
            cluster=node["cluster_name"]
        )
        output_raw = host.check_output(cmd)
        output_json = json.loads(output_raw)
        active_daemon = output_json["fsmap"]["by_rank"][0]["name"]
        if active_daemon != hostname:
            assert output_json['fsmap']['up:standby'] == 1
