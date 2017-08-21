import pytest

class TestNFSs(object):

    @pytest.mark.no_docker
    def test_nfs_ganesha_is_installed(self, node, host):
        assert host.package("nfs-ganesha").is_installed

    @pytest.mark.no_docker
    def test_nfs_ganesha_rgw_package_is_installed(self, node, host):
        assert host.package("nfs-ganesha-rgw").is_installed

    @pytest.mark.no_docker
    def test_nfs_services_are_running(self, node, host):
        assert host.service("nfs-ganesha").is_running

    @pytest.mark.no_docker
    def test_nfs_services_are_enabled(self, node, host):
        assert host.service("nfs-ganesha").is_enabled
