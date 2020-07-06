import json
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

    @pytest.mark.no_docker
    def test_nfs_config_override(self, node, host):
        assert host.file("/etc/ganesha/ganesha.conf").contains("Entries_HWMark")

    def test_nfs_is_up(self, node, host):
        hostname = node["vars"]["inventory_hostname"]
        cluster = node['cluster_name']
        container_binary = node['container_binary']
        if node['docker']:
            container_exec_cmd = '{container_binary} exec ceph-nfs-{hostname}'.format(container_binary=container_binary, hostname=hostname)
        else:
            container_exec_cmd = ''
        cmd = "sudo {container_exec_cmd} ceph --name client.rgw.{hostname} --keyring /var/lib/ceph/radosgw/{cluster}-rgw.{hostname}/keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(
            container_exec_cmd=container_exec_cmd,
            hostname=hostname,
            cluster=cluster
        )
        output = host.check_output(cmd)
        daemons = [i for i in json.loads(output)["servicemap"]["services"]["rgw-nfs"]["daemons"]]
        assert hostname in daemons

#NOTE (guits): This check must be fixed. (Permission denied error)
#    @pytest.mark.no_docker
#    def test_nfs_rgw_fsal_export(self, node, host):
#        if(host.mount_point("/mnt").exists):
#            cmd = host.run("sudo umount /mnt")
#            assert cmd.rc == 0
#        cmd = host.run("sudo mount.nfs localhost:/ceph /mnt/")
#        assert cmd.rc == 0
#        assert host.mount_point("/mnt").exists
