from mock.mock import MagicMock
import ceph_orch_apply


class TestCephOrchApply(object):

    def test_retrieve_current_spec_without_service_id(self):
        module = MagicMock()
        module.params = {'cluster': 'ceph'}
        module.run_command.return_value = (0, 'service_type: node-exporter\nservice_name: node-exporter\n', '')
        expected = {'service_type': 'node-exporter', 'placement': {'host_pattern': '*'}}

        result = ceph_orch_apply.retrieve_current_spec(module, expected)

        assert result == {'service_type': 'node-exporter', 'service_name': 'node-exporter'}
        module.run_command.assert_called_once_with(
            ['cephadm', 'shell', 'ceph', 'orch', 'ls', 'node-exporter', 'node-exporter', '--format=yaml'])
