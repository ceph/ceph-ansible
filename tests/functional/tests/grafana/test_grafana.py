import pytest


class TestGrafanas(object):

    @pytest.mark.dashboard
    @pytest.mark.no_docker
    def test_grafana_dashboard_is_installed(self, node, host):
        assert host.package("ceph-grafana-dashboards").is_installed

    @pytest.mark.dashboard
    @pytest.mark.parametrize('svc', [
        'alertmanager', 'grafana-server', 'prometheus'
    ])
    def test_grafana_service_enabled_and_running(self, node, host, svc):
        s = host.service(svc)
        assert s.is_enabled
        assert s.is_running

    @pytest.mark.dashboard
    @pytest.mark.parametrize('port', [
        '3000', '9092', '9093'
    ])
    def test_grafana_socket(self, node, host, setup, port):
        s = host.socket('tcp://%s:%s' % (setup["address"], port))
        assert s.is_listening
