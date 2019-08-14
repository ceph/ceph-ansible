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

    def test_mgr_is_up(self, node, host, setup):
        hostname = node["vars"]["inventory_hostname"]
        cluster = setup["cluster_name"]
        container_binary = setup["container_binary"]
        if node['docker']:
            container_exec_cmd = '{container_binary} exec ceph-mgr-{hostname}'.format(  # noqa E501
                hostname=hostname, container_binary=container_binary)
        else:
            container_exec_cmd = ''
        cmd = "sudo {container_exec_cmd} ceph --name mgr.{hostname} --keyring /var/lib/ceph/mgr/{cluster}-{hostname}/keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(  # noqa E501
            container_exec_cmd=container_exec_cmd,
            hostname=node["vars"]["inventory_hostname"],
            cluster=cluster
        )
        output_raw = host.check_output(cmd)
        output_json = json.loads(output_raw)

        assert output_json['mgrmap']['available']
