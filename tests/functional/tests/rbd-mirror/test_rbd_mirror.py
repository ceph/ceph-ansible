import pytest
import json


class TestRbdMirrors(object):

    @pytest.mark.rbdmirror_secondary
    @pytest.mark.no_docker
    def test_rbd_mirror_is_installed(self, node, host):
        assert host.package("rbd-mirror").is_installed

    @pytest.mark.rbdmirror_secondary
    def test_rbd_mirror_service_enabled_and_running(self, node, host):
        service_name = "ceph-rbd-mirror@rbd-mirror.{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        s = host.service(service_name)
        assert s.is_enabled
        assert s.is_running

    @pytest.mark.rbdmirror_secondary
    def test_rbd_mirror_is_up(self, node, setup, ceph_status):
        hostname = node["vars"]["inventory_hostname"]
        cluster = setup["cluster_name"]
        output = ceph_status(f'/var/lib/ceph/bootstrap-rbd-mirror/{cluster}.keyring')
        status = json.loads(output)
        daemon_ids = [i for i in status["servicemap"]["services"]
                      ["rbd-mirror"]["daemons"].keys() if i != "summary"]
        daemons = []
        for daemon_id in daemon_ids:
            daemons.append(status["servicemap"]["services"]["rbd-mirror"]
                           ["daemons"][daemon_id]["metadata"]["hostname"])
        assert hostname in daemons
