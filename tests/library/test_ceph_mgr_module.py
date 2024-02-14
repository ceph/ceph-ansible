from mock.mock import patch
from ansible.module_utils.basic import AnsibleModule
import os
import pytest
import ca_test_common
import ceph_mgr_module

fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'quay.io/ceph/daemon:latest'
fake_module = 'noup'
fake_user = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_user)
fake_mgr_module_ls_output = {"enabled_modules": ["iostat", "nfs", "restful"],
                             "disabled_modules": [{"name": "fake"}],
                             "always_on_modules": ["foo", "bar"]}


class TestCephMgrModuleModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_without_parameters(self, m_fail_json):
        ca_test_common.set_module_args({})
        m_fail_json.side_effect = ca_test_common.fail_json

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert result['msg'] == 'missing required arguments: name'

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_module,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['ceph',
                                 '-n',
                                 fake_user,
                                 '-k',
                                 fake_keyring,
                                 '--cluster',
                                 fake_cluster,
                                 'mgr', 'module',
                                 'enable', fake_module]
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch('ceph_mgr_module.get_mgr_initial_modules',
           return_value=['restful', 'iostat', 'nfs'])
    @patch('ceph_mgr_module.mgr_module_ls',
           return_value=fake_mgr_module_ls_output)
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_failure(self,
                          m_run_command,
                          m_exit_json,
                          m_mgr_module_ls,
                          m_get_mgr_initial_modules):
        ca_test_common.set_module_args({
            'name': fake_module
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = 'Error ENOENT: all mgr daemons do not support module \'{}\', pass --force to force enablement'.format(fake_module)
        m_run_command.return_value = 123, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == [['ceph',
                                  '-n',
                                  fake_user,
                                  '-k',
                                  fake_keyring,
                                  '--cluster',
                                  fake_cluster,
                                  'mgr', 'module',
                                  'enable', fake_module]]
        assert result['rc']
        assert result['stderr'] == "failed to enable module(s): noup. Error message(s):\nError ENOENT: " \
                                   "all mgr daemons do not support module 'noup', pass --force to force enablement"

    @patch('ceph_mgr_module.get_mgr_initial_modules', return_value=['restful', 'iostat', 'nfs'])
    @patch('ceph_mgr_module.mgr_module_ls', return_value=fake_mgr_module_ls_output)
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_enable_module(self, m_run_command, m_exit_json, m_mgr_module_ls, m_get_mgr_initial_modules):
        ca_test_common.set_module_args({
            'name': fake_module,
            'state': 'enable'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == []
        assert not result['rc']
        assert result['stderr'] == stderr
        assert result['stdout'] == "Successfully enabled module(s): noup"

    @patch('ceph_mgr_module.get_mgr_initial_modules', return_value=['restful', 'iostat', 'nfs'])
    @patch('ceph_mgr_module.mgr_module_ls', return_value={"enabled_modules": ["iostat", "nfs", "restful", "noup"],
                                                          "disabled_modules": [{"name": "fake"}],
                                                          "always_on_modules": ["foo", "bar"]
                                                          })
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_already_enabled_module(self, m_run_command, m_exit_json, m_mgr_module_ls, m_get_mgr_initial_modules):
        ca_test_common.set_module_args({
            'name': fake_module,
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stderr = 'module \'{}\' is already enabled'.format(fake_module)
        stdout = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == []
        assert not result['rc']
        assert result['stderr'] == ''
        assert result['stdout'] == 'Nothing to do.'

    @patch('ceph_mgr_module.get_mgr_initial_modules', return_value=['restful', 'iostat', 'nfs'])
    @patch('ceph_mgr_module.mgr_module_ls', return_value=fake_mgr_module_ls_output)
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_disable_module(self, m_run_command, m_exit_json, m_mgr_module_ls, m_get_mgr_initial_modules):
        ca_test_common.set_module_args({
            'name': fake_module,
            'state': 'disable'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == []
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == 'Successfully disabled module(s): noup'

    @patch('ceph_mgr_module.get_mgr_initial_modules', return_value=['restful', 'iostat', 'nfs'])
    @patch('ceph_mgr_module.mgr_module_ls', return_value=fake_mgr_module_ls_output)
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_disable_module_already_disabled(self, m_run_command, m_exit_json, m_mgr_module_ls, m_get_mgr_initial_modules):
        ca_test_common.set_module_args({
            'name': 'fake',
            'state': 'disable'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == []
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == 'Skipped module(s): fake'

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    @patch('ceph_mgr_module.get_mgr_initial_modules', return_value=['restful', 'iostat', 'nfs'])
    @patch('ceph_mgr_module.mgr_module_ls', return_value=fake_mgr_module_ls_output)
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_container(self, m_run_command, m_exit_json, m_mgr_module_ls, m_get_mgr_initial_modules):
        ca_test_common.set_module_args({
            'name': fake_module,
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, '', stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == [[fake_container_binary, 'run', '--rm', '--net=host',
                                  '-v', '/etc/ceph:/etc/ceph:z',
                                  '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                  '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                  '--entrypoint=ceph', fake_container_image,
                                  '-n', fake_user, '-k', fake_keyring,
                                  '--cluster', fake_cluster, 'mgr', 'module', 'enable', fake_module]]
        assert result['rc'] == rc
        assert result['stderr'] == ''
        assert result['stdout'] == 'action = enable success for the following modules: noup'

    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_get_run_dir(self, m_run_command):
        m_run_command.return_value = 0, '/var/run/ceph', ''
        assert ceph_mgr_module.get_run_dir(AnsibleModule, 'fake', 'fake') == '/var/run/ceph'

    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_get_run_dir_fail(self, m_run_command):
        m_run_command.return_value = 1, '', ''
        with pytest.raises(RuntimeError):
            ceph_mgr_module.get_run_dir(AnsibleModule, 'fake', 'fake')

    @patch('ceph_mgr_module.get_run_dir', return_value='/var/run/ceph')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_get_mgr_initial_modules(self, m_run_command, m_get_run_dir):
        m_run_command.return_value = 0, '{"mgr_initial_modules":"foo bar"}', ''
        m_get_run_dir.return_value = '/var/run/ceph'
        assert ceph_mgr_module.get_mgr_initial_modules(AnsibleModule, 'ceph', None) == ["foo", "bar"]

    @patch('ceph_mgr_module.get_run_dir', return_value='/var/run/ceph')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_get_mgr_initial_modules_fail(self, m_run_command, m_get_run_dir):
        m_run_command.return_value = 1, '', 'error'
        with pytest.raises(RuntimeError):
            ceph_mgr_module.get_mgr_initial_modules(AnsibleModule, 'ceph', None)

    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_mgr_module_ls(self, m_run_command):
        m_run_command.return_value = 0, '{}', ''
        assert ceph_mgr_module.mgr_module_ls(AnsibleModule, 'ceph', None) == {}

    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_mgr_module_ls_fail(self, m_run_command):
        m_run_command.return_value = 1, '', 'Error'
        with pytest.raises(RuntimeError):
            ceph_mgr_module.mgr_module_ls(AnsibleModule, 'ceph', None)

    @patch('ceph_mgr_module.get_mgr_initial_modules', return_value=['restful', 'iostat', 'nfs'])
    @patch('ceph_mgr_module.mgr_module_ls',
           return_value={"enabled_modules": ["iostat",
                                             "nfs",
                                             "restful",
                                             "foobar",
                                             "zabbix"],
                         "disabled_modules": [{"name": "fake"}],
                         "always_on_modules": ["foo", "bar"]})
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_mgr_module_auto(self, m_run_command, m_exit_json, m_mgr_module_ls,
                             m_get_mgr_initial_modules):
        m_run_command.return_value = 0, '', ''
        m_exit_json.side_effect = ca_test_common.exit_json
        ca_test_common.set_module_args({
            'name': ["foo", "bar"],
            'state': 'auto'
        })

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()
        result = result.value.args[0]
        assert result['stdout'] == "action = enable success for the following modules: bar,foo\n" \
                                   "action = disable success for the following modules: foobar,zabbix"
        assert result['changed']
        assert not result['rc']

    def test_get_cmd_from_reports(self):
        cmd = ceph_mgr_module.get_cmd_from_reports([("foo", 123, "", "Error", ['foo', 'bar'],),
                                                    ("bar", 456, "", "Error", ['bar', 'foo'],)])
        assert cmd == [['foo', 'bar'], ['bar', 'foo']]

    @patch('ceph_mgr_module.get_mgr_initial_modules', return_value=['restful', 'iostat', 'nfs'])
    @patch('ceph_mgr_module.mgr_module_ls', return_value=fake_mgr_module_ls_output)
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_enable_module_always_on(self, m_run_command, m_exit_json, m_mgr_module_ls, m_get_mgr_initial_modules):
        ca_test_common.set_module_args({
            'name': 'foo',
            'state': 'enable'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == []
        assert not result['rc']
        assert result['stderr'] == ''
        assert result['stdout'] == "Skipped module(s): foo"

    @patch('ceph_mgr_module.get_mgr_initial_modules', return_value=['restful', 'iostat', 'nfs'])
    @patch('ceph_mgr_module.mgr_module_ls', return_value=fake_mgr_module_ls_output)
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_enable_module_with_failure(self, m_run_command, m_exit_json, m_mgr_module_ls, m_get_mgr_initial_modules):
        ca_test_common.set_module_args({
            'name': ['fake', 'fake2'],
            'state': 'enable'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        rc = 1
        m_run_command.return_value = rc, '', 'Error'

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_mgr_module.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == [['ceph',
                                  '-n', 'client.admin',
                                  '-k', '/etc/ceph/ceph.client.admin.keyring',
                                  '--cluster', 'ceph', 'mgr', 'module',
                                  'enable', 'fake'],
                                 ['ceph', '-n', 'client.admin',
                                  '-k', '/etc/ceph/ceph.client.admin.keyring',
                                  '--cluster', 'ceph', 'mgr', 'module',
                                  'enable', 'fake2']]
        assert result['rc']
        assert result['stderr'] == 'Failed to enable module(s): fake,fake2'
        assert result['stdout'] == ''
