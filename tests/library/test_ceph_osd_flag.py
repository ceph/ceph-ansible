from mock.mock import patch
import os
import pytest
import ca_test_common
import ceph_osd_flag

fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'quay.ceph.io/ceph/daemon:latest'
fake_flag = 'noup'
fake_user = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_user)
invalid_flag = 'nofoo'


class TestCephOSDFlagModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_without_parameters(self, m_fail_json):
        ca_test_common.set_module_args({})
        m_fail_json.side_effect = ca_test_common.fail_json

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['msg'] == 'missing required arguments: name'

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_with_invalid_flag(self, m_fail_json):
        ca_test_common.set_module_args({
            'name': invalid_flag,
        })
        m_fail_json.side_effect = ca_test_common.fail_json

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['msg'] == ('value of name must be one of: noup, nodown, '
                                 'noout, nobackfill, norebalance, norecover, '
                                 'noscrub, nodeep-scrub, got: {}'.format(invalid_flag))

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_flag,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', 'set', fake_flag]
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_failure(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_flag
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = 'Error EINVAL: invalid command'
        rc = 22
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', 'set', fake_flag]
        assert result['rc'] == rc
        assert result['stderr'] == stderr

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_set_flag(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_flag,
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = '{} is set'.format(fake_flag)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', 'set', fake_flag]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_unset_flag(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_flag,
            'state': 'absent'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = '{} is unset'.format(fake_flag)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', 'unset', fake_flag]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_container(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'name': fake_flag,
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = '{} is set'.format(fake_flag)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == [fake_container_binary, 'run', '--rm', '--net=host',
                                 '-v', '/etc/ceph:/etc/ceph:z',
                                 '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                                 '-v', '/var/log/ceph/:/var/log/ceph/:z',
                                 '--entrypoint=ceph', fake_container_image,
                                 '-n', fake_user, '-k', fake_keyring,
                                 '--cluster', fake_cluster, 'osd', 'set', fake_flag]
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('state', ['present', 'absent'])
    def test_flag_noout_osd_level(self, m_run_command, m_exit_json, state):
        ca_test_common.set_module_args({
            'name': 'noout',
            'state': state,
            'level': 'osd',
            'osd': 'osd.123'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]

        assert result['cmd'] == ['ceph', '-n', 'client.admin', '-k', '/etc/ceph/ceph.client.admin.keyring',
                                 '--cluster', 'ceph', 'osd', 'add-noout' if state == 'present' else 'rm-noout', 'osd.123']
        assert result['rc'] == rc
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('state', ['present', 'absent'])
    def test_flag_noout_bucket_level(self, m_run_command, m_exit_json, state):
        ca_test_common.set_module_args({
            'name': 'noout',
            'state': state,
            'level': 'bucket',
            'bucket': 'my_osd_host_123'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['cmd'] == ['ceph', '-n', 'client.admin', '-k', '/etc/ceph/ceph.client.admin.keyring',
                                 '--cluster', 'ceph', 'osd', 'set-group' if state == 'present' else 'unset-group', 'noout', 'my_osd_host_123']
        assert result['rc'] == rc
        assert result['stderr'] == ''
        assert result['stdout'] == ''

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('state', ['present', 'absent'])
    def test_flag_noout_cluster_level(self, m_run_command, m_exit_json, state):
        ca_test_common.set_module_args({
            'name': 'noout',
            'state': state
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = ''
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['cmd'] == ['ceph', '-n', 'client.admin', '-k', '/etc/ceph/ceph.client.admin.keyring',
                                 '--cluster', 'ceph', 'osd', 'set' if state == 'present' else 'unset', 'noout']
        assert result['rc'] == rc
        assert result['stderr'] == ''
        assert result['stdout'] == ''
