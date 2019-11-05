import pytest
import json


class TestRGWs(object):

    @pytest.mark.no_docker
    def test_rgw_is_installed(self, node, host):
        result = host.package("radosgw").is_installed
        if not result:
            result = host.package("ceph-radosgw").is_installed
        assert result

    def test_rgw_service_enabled_and_running(self, node, host):
        service_name = "ceph-radosgw@rgw.{hostname}.{instance_name}".format(
            hostname=node["vars"]["inventory_hostname"],
            hostname=node["vars"]["instance_name"]
        )
        s = host.service(service_name)
        assert s.is_enabled
        assert s.is_running

    def test_rgw_is_up(self, node, host, setup):
        hostname = node["vars"]["ansible_hostname"]
        inventory_hostname = node["vars"]["inventory_hostname"]
        cluster = setup["cluster_name"]
        container_binary = setup["container_binary"]
        if node['docker']:
            container_exec_cmd = '{container_binary} exec ceph-rgw-{hostname}-rgw0'.format(  # noqa E501
                hostname=hostname, container_binary=container_binary)
        else:
            container_exec_cmd = ''
        cmd = "sudo {container_exec_cmd} ceph --name client.bootstrap-rgw --keyring /var/lib/ceph/bootstrap-rgw/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(  # noqa E501
            container_exec_cmd=container_exec_cmd,
            hostname=hostname,
            cluster=cluster
        )
        output = host.check_output(cmd)
        daemons = [i for i in json.loads(
            output)["servicemap"]["services"]["rgw"]["daemons"]]
        instance_name = "{hostname}.{inventory_hostname}".format(
            hostname=hostname,
            inventory_hostname=inventory_hostname
        )
        assert instance_name in daemons

    @pytest.mark.no_docker
    def test_rgw_http_endpoint(self, node, host, setup):
        # rgw frontends ip_addr is configured on public_interface
        ip_addr = host.interface(setup['public_interface']).addresses[0]
        assert host.socket(
            "tcp://{ip_addr}:{port}".format(ip_addr=ip_addr,
                                                port=(8080))
        ).is_listening  # noqa E501
