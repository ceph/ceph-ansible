import pytest



uses_conf_tests = pytest.mark.skipif(
    'conf_tests' not in pytest.config.slaveinput['node_config']['components'],
    reason="only run in monitors configured with initial_members"
)


class TestMon(object):

    def get_line_from_config(self, string, conf_path):
        with open(conf_path) as ceph_conf:
            ceph_conf_lines = ceph_conf.readlines()
            for line in ceph_conf_lines:
                if string in line:
                    return line.strip().strip('\n')

    @uses_conf_tests
    def test_ceph_config_has_inital_members_line(self, scenario_config):
        cluster_name = scenario_config.get('ceph', {}).get('cluster_name', 'ceph')
        ceph_conf_path = '/etc/ceph/%s.conf' % cluster_name
        initial_members_line = self.get_line_from_config('mon initial members', ceph_conf_path)
        assert initial_members_line

    @uses_conf_tests
    def test_initial_members_line_has_correct_value(self, scenario_config):
        cluster_name = scenario_config.get('ceph', {}).get('cluster_name', 'ceph')
        ceph_conf_path = '/etc/ceph/%s.conf' % cluster_name
        initial_members_line = self.get_line_from_config('mon initial members', ceph_conf_path)
        assert initial_members_line == 'mon initial members = ceph-mon0,ceph-mon1,ceph-mon2'

    @uses_conf_tests
    def test_mon_host_line_has_correct_value(self, scenario_config):
        cluster_name = scenario_config.get('ceph', {}).get('cluster_name', 'ceph')
        ceph_conf_path = '/etc/ceph/%s.conf' % cluster_name
        initial_members_line = self.get_line_from_config('mon host', ceph_conf_path)
        assert initial_members_line == 'mon host = 192.168.9.10,192.168.9.11,192.168.9.12'
