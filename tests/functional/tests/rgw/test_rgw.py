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

    def test_rgw_is_up(self, node, setup, ceph_status):
        hostname = node["vars"]["inventory_hostname"]
        cluster = setup["cluster_name"]
        name = "client.bootstrap-rgw"
        output = ceph_status(f'/var/lib/ceph/bootstrap-rgw/{cluster}.keyring', name=name)
        keys = list(json.loads(
            output)["servicemap"]["services"]["rgw"]["daemons"].keys())
        keys.remove('summary')
        daemons = json.loads(output)["servicemap"]["services"]["rgw"]["daemons"]
        hostnames = []
        for key in keys:
            hostnames.append(daemons[key]['metadata']['hostname'])
        assert hostname in hostnames

    @pytest.mark.no_docker
    def test_rgw_http_endpoint(self, node, host, setup):
        # rgw frontends ip_addr is configured on public_interface
        ip_addr = host.interface(setup['public_interface']).addresses[0]
        for i in range(int(node["radosgw_num_instances"])):
            assert host.socket(
                "tcp://{ip_addr}:{port}".format(ip_addr=ip_addr,
                                                port=(8080+i))
            ).is_listening  # noqa E501
