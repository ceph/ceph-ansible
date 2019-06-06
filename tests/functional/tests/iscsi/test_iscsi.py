import pytest


class TestiSCSIs(object):

    @pytest.mark.no_docker
    @pytest.mark.parametrize('pkg', [
        'ceph-iscsi',
        'targetcli',
        'tcmu-runner'
    ])
    def test_iscsi_package_is_installed(self, node, host, pkg):
        assert host.package(pkg).is_installed

    @pytest.mark.parametrize('svc', [
        'rbd-target-api',
        'rbd-target-gw',
        'tcmu-runner'
    ])
    def test_iscsi_service_enabled_and_running(self, node, host, svc):
        s = host.service(svc)
        assert s.is_enabled
        assert s.is_running
