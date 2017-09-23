import pytest
import json

class TestRbdMirrors(object):

    @pytest.mark.no_docker
    def test_rbd_mirror_is_installed(self, node, host):
        assert host.package("rbd-mirror").is_installed

    def test_rbd_mirror_service_is_running(self, node, host):
        service_name = "ceph-rbd-mirror@rbd-mirror.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_running

    def test_rbd_mirror_service_is_enabled(self, node, host):
        service_name = "ceph-rbd-mirror@rbd-mirror.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_enabled

    @pytest.mark.no_docker
    def test_rbd_mirror_is_up(self, node, host):
        hostname = node["vars"]["inventory_hostname"]
        cluster = node['cluster_name']
        cmd = "sudo ceph --name client.bootstrap-rbd --keyring /var/lib/ceph/bootstrap-rbd/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            hostname=hostname,
            cluster=cluster
        )
        output = host.check_output(cmd)
        daemons = [i for i in json.loads(output)["servicemap"]["services"]["rbd-mirror"]["daemons"]]
        assert hostname in daemons

    @pytest.mark.docker
    def test_docker_rbd_mirror_is_up(self, node, host):
        hostname = node["vars"]["inventory_hostname"]
        cluster = node['cluster_name']
        cmd = "sudo docker exec ceph-rbd-mirror-{hostname} ceph --name client.bootstrap-rbd --keyring /var/lib/ceph/bootstrap-rbd/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            hostname=hostname,
            cluster=cluster
        )
        output = host.check_output(cmd)
        daemons = [i for i in json.loads(output)["servicemap"]["services"]["rbd-mirror"]["daemons"]]
        assert hostname in daemons
