import pytest


class TestNodeExporter(object):

    @pytest.mark.dashboard
    def test_node_exporter_service_enabled_and_running(self, node, host):
        s = host.service("node_exporter")
        assert s.is_enabled
        assert s.is_running

    @pytest.mark.dashboard
    def test_node_exporter_socket(self, node, host):
        assert host.socket('tcp://9100').is_listening
