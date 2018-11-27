import pytest
import json


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
        hostname = node["vars"]["inventory_hostname"]
        cluster = node["cluster_name"]
        daemons = []
        if node['docker']:
            container_binary = 'docker'
            if host.exists('podman') and host.ansible("setup")["ansible_facts"]["ansible_distribution"] == 'Fedora':  # noqa E501
                container_binary = 'podman'
            docker_exec_cmd = '{container_binary} exec ceph-rbd-mirror-{hostname}'.format(  # noqa E501
                hostname=hostname, container_binary=container_binary)
        else:
            docker_exec_cmd = ''
        hostname = node["vars"]["inventory_hostname"]
        cluster = node['cluster_name']
        cmd = "sudo {docker_exec_cmd} ceph --name client.bootstrap-rbd-mirror --keyring /var/lib/ceph/bootstrap-rbd-mirror/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(  # noqa E501
            docker_exec_cmd=docker_exec_cmd,
            hostname=hostname,
            cluster=cluster
        )
        output = host.check_output(cmd)
        status = json.loads(output)
        daemon_ids = [i for i in status["servicemap"]["services"]
                      ["rbd-mirror"]["daemons"].keys() if i != "summary"]
        for daemon_id in daemon_ids:
            daemons.append(status["servicemap"]["services"]["rbd-mirror"]
                           ["daemons"][daemon_id]["metadata"]["hostname"])
        assert hostname in daemons
