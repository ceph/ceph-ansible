import pytest
import json


class TestMGRs(object):

    @pytest.mark.no_docker
    def test_mgr_is_installed(self, node, host):
        assert host.package("ceph-mgr").is_installed

    @pytest.mark.dashboard
    @pytest.mark.no_docker
    def test_mgr_dashboard_is_installed(self, node, host):
        assert host.package("ceph-mgr-dashboard").is_installed

    def test_mgr_service_is_enabled_and_running(self, node, host):
        service_name = "ceph-mgr@{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        s = host.service(service_name)
        assert s.is_enabled
        assert s.is_running

    @pytest.mark.dashboard
    @pytest.mark.parametrize('port', [
        '8443', '9283'
    ])
    def test_mgr_dashboard_is_listening(self, node, host, setup, port):
        s = host.socket('tcp://%s:%s' % (setup["address"], port))
        assert s.is_listening

    def test_mgr_is_up(self, node, setup, ceph_status):
        hostname = node["vars"]["inventory_hostname"]
        cluster = setup["cluster_name"]
        name = f"mgr.{hostname}"
        output_raw = ceph_status(f'/var/lib/ceph/mgr/{cluster}-{hostname}/keyring', name=name)
        output_json = json.loads(output_raw)

        assert output_json['mgrmap']['available']
