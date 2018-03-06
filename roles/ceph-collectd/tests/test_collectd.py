testinfra_hosts = ['!ceph-grafana']


class TestCollectd(object):
    def test_service_enabled(self, host):
        assert host.service('collectd').is_enabled
        assert host.service('collectd').is_running

    def test_logfile_present(self, host):
        assert host.file('/var/log/collectd-cephmetrics.log').is_file
