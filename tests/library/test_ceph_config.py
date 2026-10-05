import json
from mock.mock import patch
import pytest
import ca_test_common
import ceph_config

fake_cluster = 'ceph'
fake_user = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_user)

fake_config_dump = [
    {
        "section": "global",
        "mask": "",
        "can_update_at_runtime": True,
        "name": "osd_pool_default_size",
        "value": "3"
    },
    {
        "section": "osd",
        "mask": "host:osd0",
        "can_update_at_runtime": True,
        "name": "osd_memory_target",
        "value": "4294967296"
    }
]


class TestCephConfigModule(object):

    def test_get_current_value_unmasked(self):
        val = ceph_config.get_current_value('global', 'osd_pool_default_size', fake_config_dump)
        assert val == "3"

    def test_get_current_value_masked(self):
        val = ceph_config.get_current_value('osd/host:osd0', 'osd_memory_target', fake_config_dump)
        assert val == "4294967296"

    def test_get_current_value_not_found(self):
        val = ceph_config.get_current_value('osd/host:osd1', 'osd_memory_target', fake_config_dump)
        assert val is None

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_missing_required_args(self, m_fail_json):
        ca_test_common.set_module_args({})
        m_fail_json.side_effect = ca_test_common.fail_json

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            ceph_config.main()

        result = result.value.args[0]
        assert 'missing required arguments' in result['msg']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ceph_config.get_config_dump')
    def test_set_already_set(self, m_get_config_dump, m_exit_json):
        ca_test_common.set_module_args({
            'who': 'osd/host:osd0',
            'option': 'osd_memory_target',
            'value': '4294967296',
            'action': 'set'
        })
        m_get_config_dump.return_value = (0, ['ceph', 'config', 'dump'], json.dumps(fake_config_dump), '')
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_config.main()

        res = result.value.args[0]
        assert not res['changed']
        assert 'already set' in res['stdout']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ceph_config.set_option')
    @patch('ceph_config.get_config_dump')
    def test_set_needs_update(self, m_get_config_dump, m_set_option, m_exit_json):
        ca_test_common.set_module_args({
            'who': 'osd/host:osd0',
            'option': 'osd_memory_target',
            'value': '8589934592',
            'action': 'set'
        })
        m_get_config_dump.return_value = (0, ['ceph', 'config', 'dump'], json.dumps(fake_config_dump), '')
        m_set_option.return_value = (0, ['ceph', 'config', 'set'], '', '')
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_config.main()

        res = result.value.args[0]
        assert res['changed']
