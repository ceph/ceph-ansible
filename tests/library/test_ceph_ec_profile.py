from mock.mock import MagicMock, patch
import ca_test_common
import ceph_ec_profile
import pytest


class TestCephEcProfile(object):
    def setup_method(self):
        self.fake_params = []
        self.fake_binary = 'ceph'
        self.fake_cluster = 'ceph'
        self.fake_name = 'foo'
        self.fake_k = 2
        self.fake_m = 4
        self.fake_module = MagicMock()
        self.fake_module.params = self.fake_params

    def test_get_profile(self):
        expected_cmd = [
            self.fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', self.fake_cluster,
            'osd', 'erasure-code-profile',
            'get', self.fake_name,
            '--format=json'
        ]

        assert ceph_ec_profile.get_profile(self.fake_module, self.fake_name) == expected_cmd

    @pytest.mark.parametrize("stripe_unit,crush_device_class,force", [(False, None, False),
                                                                      (32, None, True),
                                                                      (False, None, True),
                                                                      (32, None, False),
                                                                      (False, 'hdd', False),
                                                                      (32, 'ssd', True),
                                                                      (False, 'nvme', True),
                                                                      (32, 'hdd', False)])
    def test_create_profile(self, stripe_unit, crush_device_class, force):
        expected_cmd = [
            self.fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', self.fake_cluster,
            'osd', 'erasure-code-profile',
            'set', self.fake_name,
            'k={}'.format(self.fake_k), 'm={}'.format(self.fake_m),
        ]
        if stripe_unit:
            expected_cmd.append('stripe_unit={}'.format(stripe_unit))
        if crush_device_class:
            expected_cmd.append('crush-device-class={}'.format(crush_device_class))
        if force:
            expected_cmd.append('--force')

        assert ceph_ec_profile.create_profile(self.fake_module,
                                              self.fake_name,
                                              self.fake_k,
                                              self.fake_m,
                                              stripe_unit,
                                              crush_device_class,
                                              self.fake_cluster,
                                              force) == expected_cmd

    def test_delete_profile(self):
        expected_cmd = [
            self.fake_binary,
            '-n', 'client.admin',
            '-k', '/etc/ceph/ceph.client.admin.keyring',
            '--cluster', self.fake_cluster,
            'osd', 'erasure-code-profile',
            'rm', self.fake_name
            ]

        assert ceph_ec_profile.delete_profile(self.fake_module,
                                              self.fake_name,
                                              self.fake_cluster) == expected_cmd

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ceph_ec_profile.exec_command')
    def test_state_present_nothing_to_update(self, m_exec_command, m_exit_json, m_fail_json):
        ca_test_common.set_module_args({"state": "present",
                                        "name": "foo",
                                        "k": 2,
                                        "m": 4,
                                        "stripe_unit": 32,
                                        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_fail_json.side_effect = ca_test_common.fail_json
        m_exec_command.return_value = (0,
                                       ['ceph', 'osd', 'erasure-code-profile', 'get', 'foo', '--format', 'json'],
                                       '{"crush-device-class":"","crush-failure-domain":"host","crush-root":"default","jerasure-per-chunk-alignment":"false","k":"2","m":"4","plugin":"jerasure","stripe_unit":"32","technique":"reed_sol_van","w":"8"}',  # noqa: E501
                                       '')

        with pytest.raises(ca_test_common.AnsibleExitJson) as r:
            ceph_ec_profile.run_module()

        result = r.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['ceph', 'osd', 'erasure-code-profile', 'get', 'foo', '--format', 'json']
        assert result['stdout'] == '{"crush-device-class":"","crush-failure-domain":"host","crush-root":"default","jerasure-per-chunk-alignment":"false","k":"2","m":"4","plugin":"jerasure","stripe_unit":"32","technique":"reed_sol_van","w":"8"}'  # noqa: E501
        assert not result['stderr']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ceph_ec_profile.exec_command')
    def test_state_present_profile_to_update(self, m_exec_command, m_exit_json, m_fail_json):
        ca_test_common.set_module_args({"state": "present",
                                        "name": "foo",
                                        "k": 2,
                                        "m": 6,
                                        "stripe_unit": 32
                                        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_fail_json.side_effect = ca_test_common.fail_json
        m_exec_command.side_effect = [
                                       (0,
                                        ['ceph', 'osd', 'erasure-code-profile', 'get', 'foo', '--format', 'json'],
                                        '{"crush-device-class":"","crush-failure-domain":"host","crush-root":"default","jerasure-per-chunk-alignment":"false","k":"2","m":"4","plugin":"jerasure","stripe_unit":"32","technique":"reed_sol_van","w":"8"}',  # noqa: E501
                                        ''),
                                       (0,
                                        ['ceph', 'osd', 'erasure-code-profile', 'set', 'foo', 'k=2', 'm=6', 'stripe_unit=32', '--force'],
                                        '',
                                        ''
                                        )
                                    ]

        with pytest.raises(ca_test_common.AnsibleExitJson) as r:
            ceph_ec_profile.run_module()

        result = r.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', 'osd', 'erasure-code-profile', 'set', 'foo', 'k=2', 'm=6', 'stripe_unit=32', '--force']
        assert not result['stdout']
        assert not result['stderr']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ceph_ec_profile.exec_command')
    def test_state_present_profile_doesnt_exist(self, m_exec_command, m_exit_json, m_fail_json):
        ca_test_common.set_module_args({"state": "present",
                                        "name": "foo",
                                        "k": 2,
                                        "m": 4,
                                        "stripe_unit": 32
                                        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_fail_json.side_effect = ca_test_common.fail_json
        m_exec_command.side_effect = [
                                       (2,
                                        ['ceph', 'osd', 'erasure-code-profile', 'get', 'foo', '--format', 'json'],
                                        '',
                                        "Error ENOENT: unknown erasure code profile 'foo'"),
                                       (0,
                                        ['ceph', 'osd', 'erasure-code-profile', 'set', 'foo', 'k=2', 'm=4', 'stripe_unit=32', '--force'],
                                        '',
                                        ''
                                        )
                                    ]

        with pytest.raises(ca_test_common.AnsibleExitJson) as r:
            ceph_ec_profile.run_module()

        result = r.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', 'osd', 'erasure-code-profile', 'set', 'foo', 'k=2', 'm=4', 'stripe_unit=32', '--force']
        assert not result['stdout']
        assert not result['stderr']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ceph_ec_profile.exec_command')
    def test_state_absent_on_existing_profile(self, m_exec_command, m_exit_json, m_fail_json):
        ca_test_common.set_module_args({"state": "absent",
                                        "name": "foo"
                                        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_fail_json.side_effect = ca_test_common.fail_json
        m_exec_command.return_value = (0,
                                       ['ceph', 'osd', 'erasure-code-profile', 'rm', 'foo'],
                                       '',
                                       '')

        with pytest.raises(ca_test_common.AnsibleExitJson) as r:
            ceph_ec_profile.run_module()

        result = r.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', 'osd', 'erasure-code-profile', 'rm', 'foo']
        assert result['stdout'] == 'Profile foo removed.'
        assert not result['stderr']
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ceph_ec_profile.exec_command')
    def test_state_absent_on_nonexisting_profile(self, m_exec_command, m_exit_json, m_fail_json):
        ca_test_common.set_module_args({"state": "absent",
                                        "name": "foo"
                                        })
        m_exit_json.side_effect = ca_test_common.exit_json
        m_fail_json.side_effect = ca_test_common.fail_json
        m_exec_command.return_value = (0,
                                       ['ceph', 'osd', 'erasure-code-profile', 'rm', 'foo'],
                                       '',
                                       'erasure-code-profile foo does not exist')

        with pytest.raises(ca_test_common.AnsibleExitJson) as r:
            ceph_ec_profile.run_module()

        result = r.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['ceph', 'osd', 'erasure-code-profile', 'rm', 'foo']
        assert result['stdout'] == "Skipping, the profile foo doesn't exist"
        assert result['stderr'] == 'erasure-code-profile foo does not exist'
        assert result['rc'] == 0

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_check_mode(self, m_exit_json):
        ca_test_common.set_module_args({
            'name': 'foo',
            'k': 2,
            'm': 4,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_ec_profile.run_module()

        result = result.value.args[0]
        assert not result['changed']
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']
