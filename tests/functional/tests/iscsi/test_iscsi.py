import pytest
import json


class TestiSCSIs(object):

    @pytest.mark.no_docker
    def test_tcmu_runner_is_installed(self, node, host):
        assert host.package("tcmu-runner").is_installed

    @pytest.mark.no_docker
    def test_rbd_target_api_is_installed(self, node, host):
        assert host.package("rbd-target-api").is_installed

    @pytest.mark.no_docker
    def test_rbd_target_gw_is_installed(self, node, host):
        assert host.package("rbd-target-gw").is_installed

    def test_tcmu_runner_service_is_running(self, node, host):
        service_name = "tcmu-runner"
        assert host.service(service_name).is_running

    def test_rbd_target_api_service_is_running(self, node, host):
        service_name = "rbd-target-api"
        assert host.service(service_name).is_running

    def test_rbd_target_gw_service_is_running(self, node, host):
        service_name = "rbd-target-gw"
        assert host.service(service_name).is_running

    def test_tcmu_runner_service_is_enabled(self, node, host):
        service_name = "tcmu-runner"
        assert host.service(service_name).is_enabled

    def test_rbd_target_api_service_is_enabled(self, node, host):
        service_name = "rbd-target-api"
        assert host.service(service_name).is_enabled

    def test_rbd_target_gw_service_is_enabled(self, node, host):
        service_name = "rbd-target-gw"
        assert host.service(service_name).is_enabled
