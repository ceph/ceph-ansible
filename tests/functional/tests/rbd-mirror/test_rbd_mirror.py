import pytest
import json


class TestRbdMirrors(object):

    @pytest.mark.no_docker
    def test_rbd_mirror_is_installed(self, node, host):
        assert host.package("rbd-mirror").is_installed

    def test_rbd_mirror_service_enabled_and_running(self, node, host):
        service_name = "ceph-rbd-mirror@rbd-mirror.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        s = host.service(service_name)
        assert s.is_enabled
        assert s.is_running

    def test_rbd_mirror_is_up(self, node, host, setup):
        hostname = node["vars"]["inventory_hostname"]
        cluster = setup["cluster_name"]
        container_binary = setup["container_binary"]
        daemons = []
        if node['docker']:
            container_exec_cmd = '{container_binary} exec ceph-rbd-mirror-{hostname}'.format(  # noqa E501
                hostname=hostname, container_binary=container_binary)
        else:
            container_exec_cmd = ''
        hostname = node["vars"]["inventory_hostname"]
        cluster = setup['cluster_name']
        cmd = "sudo {container_exec_cmd} ceph --name client.bootstrap-rbd-mirror --keyring /var/lib/ceph/bootstrap-rbd-mirror/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(  # noqa E501
            container_exec_cmd=container_exec_cmd,
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
