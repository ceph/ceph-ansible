import json
import pytest


class TestNFSs(object):

    @pytest.mark.no_docker
    @pytest.mark.parametrize('pkg', [
        'nfs-ganesha',
        'nfs-ganesha-rgw'
    ])
    def test_nfs_ganesha_package_is_installed(self, node, host, pkg):
        assert host.package(pkg).is_installed

    @pytest.mark.no_docker
    def test_nfs_service_enabled_and_running(self, node, host):
        s = host.service("nfs-ganesha")
        assert s.is_enabled
        assert s.is_running

    @pytest.mark.no_docker
    def test_nfs_config_override(self, node, host):
        assert host.file(
            "/etc/ganesha/ganesha.conf").contains("Entries_HWMark")

    def test_nfs_is_up(self, node, setup, ceph_status):
        hostname = node["vars"]["inventory_hostname"]
        cluster = setup["cluster_name"]
        name = f"client.rgw.{hostname}"
        output = ceph_status(f'/var/lib/ceph/radosgw/{cluster}-rgw.{hostname}/keyring', name=name)
        keys = list(json.loads(
            output)["servicemap"]["services"]["rgw-nfs"]["daemons"].keys())
        keys.remove('summary')
        daemons = json.loads(output)["servicemap"]["services"]["rgw-nfs"]["daemons"]
        hostnames = []
        for key in keys:
            hostnames.append(daemons[key]['metadata']['hostname'])


# NOTE (guits): This check must be fixed. (Permission denied error)
#    @pytest.mark.no_docker
#    def test_nfs_rgw_fsal_export(self, node, host):
#        if(host.mount_point("/mnt").exists):
#            cmd = host.run("sudo umount /mnt")
#            assert cmd.rc == 0
#        cmd = host.run("sudo mount.nfs localhost:/ceph /mnt/")
#        assert cmd.rc == 0
#        assert host.mount_point("/mnt").exists
