import pytest


class TestCephFSMirror(object):

    @pytest.mark.cephfsmirrors
    @pytest.mark.no_docker
    def test_cephfs_mirror_is_installed(self, host):
        assert host.package("cephfs-mirror").is_installed

    @pytest.mark.cephfsmirrors
    def test_cephfs_mirror_service_enabled_and_running(self, node, host):
        daemon_id = node["vars"].get("ceph_cephfs_mirror_daemon_id", "mirror")
        service_name = (
            f"ceph-cephfs-mirror@{daemon_id}"
            if node["docker"]
            else f"cephfs-mirror@{daemon_id}"
        )
        service = host.service(service_name)
        assert service.is_enabled
        assert service.is_running

    @pytest.mark.cephfsmirrors
    def test_cephfs_mirror_keyring_exists(self, node, host, setup):
        cluster = setup["cluster_name"]
        daemon_id = node["vars"].get("ceph_cephfs_mirror_daemon_id", "mirror")
        keyring = host.file(f"/etc/ceph/{cluster}.client.{daemon_id}.keyring")
        assert keyring.exists
        assert keyring.is_file
