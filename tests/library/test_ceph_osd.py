from mock.mock import patch
import os
import pytest
import ca_test_common
import ceph_osd

fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'quay.io/ceph/daemon:latest'
fake_id = '42'
fake_ids = ['0', '7', '13']
fake_user = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_user)
invalid_state = 'foo'


class TestCephOSDModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_without_parameters(self, m_fail_json):
        ca_test_common.set_module_args({})
        m_fail_json.side_effect = ca_test_common.fail_json

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            ceph_osd.main()

        result = result.value.args[0]
        assert result['msg'] == 'missing required arguments: ids, state'

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_with_invalid_state(self, m_fail_json):
        ca_test_common.set_module_args({
            'ids': fake_id,
            'state': invalid_state,
        })
        m_fail_json.side_effect = ca_test_common.fail_json

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            ceph_osd.main()

        result = result.value.args[0]
        assert result['msg'] == ('value of state must be one of: destroy, down, '
                                 'in, out, purge, rm, got: {}'.format(invalid_state))

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        ca_test_common.set_module_args({
            'ids': fake_id,
            'state': 'rm',
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = ca_test_common.exit_json

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', 'rm', fake_id]
        assert result['rc'] == 0
        assert not result['stdout']
        assert not result['stderr']

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_with_failure(self, m_run_command, m_exit_json):
        ca_test_common.set_module_args({
            'ids': fake_id,
            'state': 'rm'
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = 'Error EBUSY: osd.{} is still up; must be down before removal.'.format(fake_id)
        rc = 16
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', 'rm', fake_id]
        assert result['rc'] == rc
        assert result['stderr'] == stderr

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('state', ['destroy', 'down', 'in', 'out', 'purge', 'rm'])
    def test_set_state(self, m_run_command, m_exit_json, state):
        ca_test_common.set_module_args({
            'ids': fake_id,
            'state': state
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = 'marked {} osd.{}'.format(state, fake_id)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr
        cmd = ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', state, fake_id]
        if state in ['destroy', 'purge']:
            cmd.append('--yes-i-really-mean-it')

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('state', ['down', 'in', 'out', 'rm'])
    def test_set_state_multiple_ids(self, m_run_command, m_exit_json, state):
        ca_test_common.set_module_args({
            'ids': fake_ids,
            'state': state
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stderr = ''
        stdout = ''
        for osd in fake_ids:
            stderr += 'marked {} osd.{} '.format(state, osd)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr
        cmd = ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', state]
        cmd.extend(fake_ids)

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('state', ['destroy', 'purge'])
    def test_invalid_state_multiple_ids(self, m_run_command, m_fail_json, state):
        ca_test_common.set_module_args({
            'ids': fake_ids,
            'state': state
        })
        m_fail_json.side_effect = ca_test_common.fail_json

        with pytest.raises(ca_test_common.AnsibleFailJson) as result:
            ceph_osd.main()

        result = result.value.args[0]
        assert result['msg'] == 'destroy and purge only support one OSD at at time'
        assert result['rc'] == 1

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('state', ['down', 'in', 'out'])
    def test_already_set_state(self, m_run_command, m_exit_json, state):
        ca_test_common.set_module_args({
            'ids': fake_id,
            'state': state
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = 'osd.{} is already {}.'.format(fake_id, state)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr
        cmd = ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', state, fake_id]

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd.main()

        result = result.value.args[0]
        assert not result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('state', ['down', 'in', 'out', 'rm'])
    def test_one_already_set_state_multiple_ids(self, m_run_command, m_exit_json, state):
        ca_test_common.set_module_args({
            'ids': fake_ids,
            'state': state
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = 'marked {} osd.{}. osd.{} does not exist. osd.{} does not exist.'.format(state, fake_ids[0], fake_ids[1], fake_ids[2])
        rc = 0
        m_run_command.return_value = rc, stdout, stderr
        cmd = ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', state]
        cmd.extend(fake_ids)
        if state in ['destroy', 'purge']:
            cmd.append('--yes-i-really-mean-it')

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout

    @patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': fake_container_binary})
    @patch.dict(os.environ, {'CEPH_CONTAINER_IMAGE': fake_container_image})
    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    @pytest.mark.parametrize('state', ['destroy', 'down', 'in', 'out', 'purge', 'rm'])
    def test_set_state_with_container(self, m_run_command, m_exit_json, state):
        ca_test_common.set_module_args({
            'ids': fake_id,
            'state': state
        })
        m_exit_json.side_effect = ca_test_common.exit_json
        stdout = ''
        stderr = 'marked {} osd.{}'.format(state, fake_id)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr
        cmd = [fake_container_binary, 'run', '--rm', '--net=host',
               '-v', '/etc/ceph:/etc/ceph:z',
               '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
               '-v', '/var/log/ceph/:/var/log/ceph/:z',
               '--entrypoint=ceph', fake_container_image,
               '-n', fake_user, '-k', fake_keyring,
               '--cluster', fake_cluster, 'osd', state, fake_id]
        if state in ['destroy', 'purge']:
            cmd.append('--yes-i-really-mean-it')

        with pytest.raises(ca_test_common.AnsibleExitJson) as result:
            ceph_osd.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == cmd
        assert result['rc'] == rc
        assert result['stderr'] == stderr
        assert result['stdout'] == stdout
