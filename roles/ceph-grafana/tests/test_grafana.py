import json
import os
import pytest

testinfra_hosts = ['ceph-grafana']


class TestGrafana(object):
    def get_ceph_hosts(self, host):
        """
        Extract a list of FQDNs of Ceph hosts from the Ansible inventory
        """
        groups = host.ansible.get_variables()['groups']
        ceph_groups = ('mdss', 'mgrs', 'mons', 'osds', 'rgws')
        ceph_hosts = set()
        for group in ceph_groups:
            hosts = groups.get(group, list())
            map(ceph_hosts.add, hosts)
        return list(ceph_hosts)

    @pytest.mark.parametrize(
        "service",
        ['carbon-cache',
         dict(apt='apache2', yum='httpd'),
         'grafana-server']
    )
    def test_service_enabled(self, host, service):
        """ Are the proper services enabled? """
        if isinstance(service, dict):
            service = service[
                host.ansible('setup')['ansible_facts']['ansible_pkg_mgr']]
        service = host.service(service)
        assert service.is_running
        assert service.is_enabled

    @pytest.mark.parametrize(
        "proto,iface,port",
        [
            ('tcp', '0.0.0.0', '2003'),  # carbon
            ('tcp', '0.0.0.0', '2004'),  # carbon
            ('tcp', '0.0.0.0', '8080'),  # graphite
            ('tcp', '0.0.0.0', '3000'),  # grafana
        ]
    )
    def test_ports_open(self, host, proto, iface, port):
        """ Are the proper ports open? """
        socket_spec = "%s://%s" % (proto, iface)
        if iface:
            socket_spec += ':'
        socket_spec += port
        assert host.socket(socket_spec).is_listening

    def test_whisper_data(self, host):
        """ Does whisper data exist for each Ceph host? """
        whisper_dirs = [
            '/var/lib/carbon/whisper',
            '/var/lib/graphite/whisper',
        ]
        for whisper_dir in whisper_dirs:
            if host.file(whisper_dir).exists:
                break
        for ceph_host in self.get_ceph_hosts(host):
            whisper_subdir = os.path.join(
                whisper_dir, 'collectd', ceph_host.replace('.', '/')
            )
            assert host.file(whisper_subdir).is_directory
            cpu_metrics = [
                'idle.wsp', 'nice.wsp', 'steal.wsp', 'user.wsp',
                'interrupt.wsp', 'softirq.wsp', 'system.wsp', 'wait.wsp',
            ]
            assert any([
                host.file(os.path.join(
                    whisper_subdir, 'cpu', 'percent', metric
                )).is_file for metric in cpu_metrics
            ])

    def test_metrics_present(self, host):
        """ Does graphite know about each Ceph host? """
        ceph_hosts = self.get_ceph_hosts(host)
        out = host.check_output(
            "curl http://localhost:8080/metrics/find?query=collectd.*")
        obj = json.loads(out)

        def extract_hostname(fragment):
            return fragment['text']
        metric_hosts = map(extract_hostname, obj)
        assert sorted(map(lambda s: s.split('.')[0], ceph_hosts)) == \
            sorted(metric_hosts)
