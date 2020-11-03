from mock.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import os
import json
import pytest
import ceph_osd_flag

fake_cluster = 'ceph'
fake_container_binary = 'podman'
fake_container_image = 'quay.ceph.io/ceph/daemon:latest'
fake_flag = 'noup'
fake_user = 'client.admin'
fake_keyring = '/etc/ceph/{}.{}.keyring'.format(fake_cluster, fake_user)
invalid_flag = 'nofoo'


def set_module_args(args):
    if '_ansible_remote_tmp' not in args:
        args['_ansible_remote_tmp'] = '/tmp'
    if '_ansible_keep_remote_files' not in args:
        args['_ansible_keep_remote_files'] = False

    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    raise AnsibleFailJson(kwargs)


class TestCephOSDFlagModule(object):

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_without_parameters(self, m_fail_json):
        set_module_args({})
        m_fail_json.side_effect = fail_json

        with pytest.raises(AnsibleFailJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['msg'] == 'missing required arguments: name'

    @patch('ansible.module_utils.basic.AnsibleModule.fail_json')
    def test_with_invalid_flag(self, m_fail_json):
        set_module_args({
            'name': invalid_flag,
        })
        m_fail_json.side_effect = fail_json

        with pytest.raises(AnsibleFailJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['msg'] == ('value of name must be one of: noup, nodown, '
                                 'noout, nobackfill, norebalance, norecover, '
                                 'noscrub, nodeep-scrub, got: {}'.format(invalid_flag))

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    def test_with_check_mode(self, m_exit_json):
        set_module_args({
            'name': fake_flag,
            '_ansible_check_mode': True
        })
        m_exit_json.side_effect = exit_json

        with pytest.raises(AnsibleExitJson) as result:
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
        set_module_args({
            'name': fake_flag
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = 'Error EINVAL: invalid command'
        rc = 22
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
            ceph_osd_flag.main()

        result = result.value.args[0]
        assert result['changed']
        assert result['cmd'] == ['ceph', '-n', fake_user, '-k', fake_keyring, '--cluster', fake_cluster, 'osd', 'set', fake_flag]
        assert result['rc'] == rc
        assert result['stderr'] == stderr

    @patch('ansible.module_utils.basic.AnsibleModule.exit_json')
    @patch('ansible.module_utils.basic.AnsibleModule.run_command')
    def test_set_flag(self, m_run_command, m_exit_json):
        set_module_args({
            'name': fake_flag,
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = '{} is set'.format(fake_flag)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
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
        set_module_args({
            'name': fake_flag,
            'state': 'absent'
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = '{} is unset'.format(fake_flag)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
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
        set_module_args({
            'name': fake_flag,
        })
        m_exit_json.side_effect = exit_json
        stdout = ''
        stderr = '{} is set'.format(fake_flag)
        rc = 0
        m_run_command.return_value = rc, stdout, stderr

        with pytest.raises(AnsibleExitJson) as result:
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
