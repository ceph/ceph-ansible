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

    def test_nfs_is_up(self, node, host, setup):
        hostname = node["vars"]["inventory_hostname"]
        cluster = setup['cluster_name']
        container_binary = setup["container_binary"]
        if node['docker']:
            container_exec_cmd = '{container_binary} exec ceph-nfs-{hostname}'.format(  # noqa E501
                hostname=hostname, container_binary=container_binary)
        else:
            container_exec_cmd = ''
        cmd = "sudo {container_exec_cmd} ceph --name client.rgw.{hostname} --keyring /var/lib/ceph/radosgw/{cluster}-rgw.{hostname}/keyring --cluster={cluster} --connect-timeout 5 -f json -s".format(  # noqa E501
            container_exec_cmd=container_exec_cmd,
            hostname=hostname,
            cluster=cluster
        )
        output = host.check_output(cmd)
        daemons = [i for i in json.loads(
            output)["servicemap"]["services"]["rgw-nfs"]["daemons"]]
        assert hostname in daemons

# NOTE (guits): This check must be fixed. (Permission denied error)
#    @pytest.mark.no_docker
#    def test_nfs_rgw_fsal_export(self, node, host):
#        if(host.mount_point("/mnt").exists):
#            cmd = host.run("sudo umount /mnt")
#            assert cmd.rc == 0
#        cmd = host.run("sudo mount.nfs localhost:/ceph /mnt/")
#        assert cmd.rc == 0
#        assert host.mount_point("/mnt").exists
