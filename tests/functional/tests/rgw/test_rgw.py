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
        for i in range(int(node["radosgw_num_instances"])):
            service_name = "ceph-radosgw@rgw.{hostname}.rgw{seq}".format(
                hostname=node["vars"]["inventory_hostname"],
                seq=i
            )
            s = host.service(service_name)
            assert s.is_enabled
            assert s.is_running

    def test_rgw_is_up(self, node, host, setup):
        hostname = node["vars"]["inventory_hostname"]
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
        for i in range(int(node["radosgw_num_instances"])):
            instance_name = "{hostname}.rgw{seq}".format(
                hostname=hostname,
                seq=i
            )
            assert instance_name in daemons

    @pytest.mark.no_docker
    def test_rgw_http_endpoint(self, node, host, setup):
        # rgw frontends ip_addr is configured on public_interface
        ip_addr = host.interface(setup['public_interface']).addresses[0]
        for i in range(int(node["radosgw_num_instances"])):
            assert host.socket(
                "tcp://{ip_addr}:{port}".format(ip_addr=ip_addr,
                                                port=(8080+i))
            ).is_listening  # noqa E501
