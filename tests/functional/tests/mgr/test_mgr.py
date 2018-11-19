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

    def test_mgr_is_up(self, node, host):
        hostname = node["vars"]["inventory_hostname"]
        cluster = node["cluster_name"]
        if node['docker']:
            container_binary = 'docker'
            if host.exists('podman') and host.ansible("setup")["ansible_facts"]["ansible_distribution"] == 'Fedora':  # noqa E501
                container_binary = 'podman'
            docker_exec_cmd = '{container_binary} exec ceph-mgr-{hostname}'.format(
                hostname=hostname, container_binary=container_binary)
        else:
            docker_exec_cmd = ''
        cmd = "sudo {docker_exec_cmd} ceph --name mgr.{hostname} --keyring /var/lib/ceph/mgr/{cluster}-{hostname}/keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            docker_exec_cmd=docker_exec_cmd,
            hostname=node["vars"]["inventory_hostname"],
            cluster=cluster
        )
        output_raw = host.check_output(cmd)
        output_json = json.loads(output_raw)
        daemons = output_json['mgrmap']['active_name']
        standbys = [i['name'] for i in output_json['mgrmap']['standbys']]
        result = hostname in daemons
        if not result:
            result = hostname in standbys
        assert result
