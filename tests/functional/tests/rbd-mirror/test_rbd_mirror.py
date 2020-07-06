import pytest
import json
import os

class TestRbdMirrors(object):

    @pytest.mark.no_docker
    def test_rbd_mirror_is_installed(self, node, host):
        assert host.package("rbd-mirror").is_installed

    @pytest.mark.docker
    def test_rbd_mirror_service_is_running_docker(self, node, host):
        service_name = "ceph-rbd-mirror@rbd-mirror.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_running

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

    def test_rbd_mirror_is_up(self, node, host):
        hostname=node["vars"]["inventory_hostname"]
        cluster=node["cluster_name"]
        container_binary = node["container_binary"]
        daemons = []
        if node['docker']:
            container_exec_cmd = '{container_binary} exec ceph-rbd-mirror-{hostname}'.format(container_binary=container_binary, hostname=hostname)
        else:
            container_exec_cmd = ''
        hostname = node["vars"]["inventory_hostname"]
        cluster = node['cluster_name']
        cmd = "sudo {container_exec_cmd} ceph --name client.bootstrap-rbd --keyring /var/lib/ceph/bootstrap-rbd/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            container_exec_cmd=container_exec_cmd,
            hostname=hostname,
            cluster=cluster
        )
        output = host.check_output(cmd)
        status = json.loads(output)
        daemon_ids = [i for i in status["servicemap"]["services"]["rbd-mirror"]["daemons"].keys() if i != "summary"]
        for daemon_id in daemon_ids:
            daemons.append(status["servicemap"]["services"]["rbd-mirror"]["daemons"][daemon_id]["metadata"]["hostname"])
        assert hostname in daemons