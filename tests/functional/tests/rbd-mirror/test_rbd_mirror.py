import pytest
import json
import os

class TestRbdMirrors(object):

    @pytest.mark.no_docker
    def test_rbd_mirror_is_installed(self, node, host):
        assert host.package("rbd-mirror").is_installed

    @pytest.mark.no_docker
    @pytest.mark.before_luminous
    def test_rbd_mirror_service_is_running_before_luminous(self, node, host):
        service_name = "ceph-rbd-mirror@admin"
        assert host.service(service_name).is_running

    @pytest.mark.docker
    @pytest.mark.before_luminous
    def test_rbd_mirror_service_is_running_docker_before_luminous(self, node, host):
        service_name = "ceph-rbd-mirror@rbd-mirror.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_running

    @pytest.mark.docker
    @pytest.mark.from_luminous
    def test_rbd_mirror_service_is_running_docker_from_luminous(self, node, host):
        service_name = "ceph-rbd-mirror@rbd-mirror.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_running

    @pytest.mark.from_luminous
    def test_rbd_mirror_service_is_running_from_luminous(self, node, host):
        service_name = "ceph-rbd-mirror@rbd-mirror.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_running

    @pytest.mark.no_docker
    @pytest.mark.before_luminous
    def test_rbd_mirror_service_is_enabled_before_luminous(self, node, host):
        service_name = "ceph-rbd-mirror@admin"
        assert host.service(service_name).is_enabled

    @pytest.mark.docker
    @pytest.mark.before_luminous
    def test_rbd_mirror_service_is_enabled_docker_before_luminous(self, node, host):
        service_name = "ceph-rbd-mirror@rbd-mirror.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_enabled

    @pytest.mark.from_luminous
    def test_rbd_mirror_service_is_enabled_from_luminous(self, node, host):
        service_name = "ceph-rbd-mirror@rbd-mirror.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        assert host.service(service_name).is_enabled

    @pytest.mark.from_luminous
    def test_rbd_mirror_is_up(self, node, host):
        ceph_release_num=node['ceph_release_num']
        ceph_stable_release=node['ceph_stable_release']
        hostname=node["vars"]["inventory_hostname"]
        cluster=node["cluster_name"]
        rolling_update=node["rolling_update"]
        daemons = []
        if node['docker']:
            docker_exec_cmd = 'docker exec ceph-rbd-mirror-{hostname}'.format(hostname=hostname)
        else:
            docker_exec_cmd = ''
        hostname = node["vars"]["inventory_hostname"]
        cluster = node['cluster_name']
        cmd = "sudo {docker_exec_cmd} ceph --name client.bootstrap-rbd --keyring /var/lib/ceph/bootstrap-rbd/{cluster}.keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            docker_exec_cmd=docker_exec_cmd,
            hostname=hostname,
            cluster=cluster
        )
        output = host.check_output(cmd)
        status = json.loads(output)
        daemon_ids = [i for i in status["servicemap"]["services"]["rbd-mirror"]["daemons"].keys() if i != "summary"]
        if ceph_release_num[ceph_stable_release] > ceph_release_num['luminous'] or (ceph_release_num[ceph_stable_release] == ceph_release_num['luminous'] and rolling_update=='True'):
            for daemon_id in daemon_ids:
                daemons.append(status["servicemap"]["services"]["rbd-mirror"]["daemons"][daemon_id]["metadata"]["hostname"])
            result = hostname in daemons
        else:
            result = hostname in daemon_ids
        assert result