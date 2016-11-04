import pytest



uses_mon_initial_members = pytest.mark.skipif(
    'mon_initial_members' not in pytest.config.slaveinput['node_config']['components'],
    reason="only run in monitors configured with initial_members"
)


class TestMon(object):

    def get_line_from_config(self, string, conf_path):
        with open(conf_path) as ceph_conf:
            ceph_conf_lines = ceph_conf.readlines()
            for line in ceph_conf_lines:
                if string in line:
                    return line.strip().strip('\n')

    @uses_mon_initial_members
    def test_ceph_config_has_inital_members_line(self, scenario_config):
        cluster_name = scenario_config.get('ceph', {}).get('cluster_name', 'ceph')
        ceph_conf_path = '/etc/ceph/%s.conf' % cluster_name
        initial_members_line = self.get_line_from_config('mon initial members', ceph_conf_path)
        assert initial_members_line

    @uses_mon_initial_members
    def test_initial_members_line_has_correct_value(self, scenario_config):
        cluster_name = scenario_config.get('ceph', {}).get('cluster_name', 'ceph')
        ceph_conf_path = '/etc/ceph/%s.conf' % cluster_name
        initial_members_line = self.get_line_from_config('mon initial members', ceph_conf_path)
        assert initial_members_line == 'mon initial members = ceph-mon0'
