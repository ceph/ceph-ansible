import pytest
import json

class TestRGWs(object):

    @pytest.mark.no_docker
    def test_rgw_is_installed(self, node, host):
        result = host.package("radosgw").is_installed
        if not result:
            result = host.package("ceph-radosgw").is_installed
        assert result

    def test_rgw_service_is_running(self, node, host):
        service_name = "ceph-radosgw@rgw.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_running

    def test_rgw_service_is_enabled(self, node, host):
        service_name = "ceph-radosgw@rgw.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_enabled

    def test_rgw_is_up(self, node, host):
        hostname = node["vars"]["inventory_hostname"]
        cluster = node["cluster_name"]
        if node['docker']:
            container_binary = 'docker'
            if host.exists('podman') and host.ansible("setup")["ansible_facts"]["ansible_distribution"] == 'Fedora':  # noqa E501
                container_binary = 'podman'
            docker_exec_cmd = '{container_binary} exec ceph-rgw-{hostname}'.format(
                hostname=hostname, container_binary=container_binary)
        else:
            docker_exec_cmd = ''
        cmd = "sudo {docker_exec_cmd} ceph --name client.bootstrap-rgw --keyring /var/lib/ceph/bootstrap-rgw/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            docker_exec_cmd=docker_exec_cmd,
            hostname=hostname,
            cluster=cluster
        )
        output = host.check_output(cmd)
        daemons = [i for i in json.loads(output)["servicemap"]["services"]["rgw"]["daemons"]]
        assert hostname in daemons

    @pytest.mark.no_docker
    def test_rgw_http_endpoint(self, node, host):
        # rgw frontends ip_addr is configured on eth1
        ip_addr = host.interface("eth1").addresses[0]
        assert host.socket("tcp://{ip_addr}:{port}".format(ip_addr=ip_addr, port=8080)).is_listening
