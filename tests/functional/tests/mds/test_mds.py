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

    def test_mds_is_up(self, node, host):
        hostname = node["vars"]["inventory_hostname"]
        container_binary = node['container_binary']
        if node['docker']:
            container_exec_cmd = '{container_binary} exec ceph-mds-{hostname}'.format(  # noqa E501
                hostname=hostname, container_binary=container_binary)
        else:
            container_exec_cmd = ''

        cmd = "sudo {container_exec_cmd} ceph --name client.bootstrap-mds --keyring /var/lib/ceph/bootstrap-mds/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            container_exec_cmd=container_exec_cmd,
            cluster=node['cluster_name']
        )
        cluster_status = json.loads(host.check_output(cmd))
        assert (cluster_status['fsmap'].get('up', 0) + cluster_status['fsmap'].get('up:standby', 0)) == len(node["vars"]["groups"]["mdss"])
