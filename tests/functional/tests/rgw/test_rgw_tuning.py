import pytest
import json


class TestRGWs(object):

    @pytest.mark.no_docker
    def test_rgw_bucket_default_quota_is_set(self, node, host, setup):
        assert host.file(setup["conf_path"]).contains(
            "rgw override bucket index max shards")
        assert host.file(setup["conf_path"]).contains(
            "rgw bucket default quota max objects")

    @pytest.mark.no_docker
    def test_rgw_bucket_default_quota_is_applied(self, node, host, setup):
        radosgw_admin_cmd = "timeout --foreground -s KILL 5 sudo radosgw-admin --cluster={cluster} -n client.rgw.{hostname}.rgw0 --keyring /var/lib/ceph/radosgw/{cluster}-rgw.{hostname}.rgw0/keyring user info --uid=test --format=json".format(  # noqa E501
            hostname=node["vars"]["inventory_hostname"],
            cluster=setup['cluster_name']
        )
        radosgw_admin_output = host.run(radosgw_admin_cmd)
        if radosgw_admin_output.rc == 22:
            radosgw_admin_cmd = "timeout --foreground -s KILL 5 sudo radosgw-admin --cluster={cluster} -n client.rgw.{hostname}.rgw0 --keyring /var/lib/ceph/radosgw/{cluster}-rgw.{hostname}.rgw0/keyring user create --uid=test --display-name Test".format(  # noqa E501
                hostname=node["vars"]["inventory_hostname"],
                cluster=setup['cluster_name']
            )
            radosgw_admin_output = host.run(radosgw_admin_cmd)
        radosgw_admin_output_json = json.loads(radosgw_admin_output.stdout)
        assert radosgw_admin_output_json["bucket_quota"]["enabled"] == True  # noqa E501
        assert radosgw_admin_output_json["bucket_quota"]["max_objects"] == 1638400  # noqa E501

    @pytest.mark.no_docker
    def test_rgw_tuning_pools_are_set(self, node, host, setup):
        pools = node["vars"]["rgw_create_pools"]
        if pools is None:
            pytest.skip('rgw_create_pools not defined, nothing to test')
        for pool_name in pools.keys():
            cmd = host.run("sudo ceph --cluster={cluster} --connect-timeout 5 -n client.rgw.{hostname}.rgw0 --keyring /var/lib/ceph/radosgw/{cluster}-rgw.{hostname}.rgw0/keyring osd pool get {pool_name} size".format(  # noqa E501
                hostname=node["vars"]["inventory_hostname"],
                cluster=setup['cluster_name'],
                pool_name=pool_name
            ))
            assert cmd.rc == 0

    @pytest.mark.docker
    def test_docker_rgw_tuning_pools_are_set(self, node, host, setup):
        hostname = node["vars"]["inventory_hostname"]
        cluster = setup['cluster_name']
        container_binary = setup["container_binary"]
        pools = node["vars"].get("rgw_create_pools")
        if pools is None:
            pytest.skip('rgw_create_pools not defined, nothing to test')
        for pool_name in pools.keys():
            cmd = host.run("sudo {container_binary} exec ceph-rgw-{hostname}-rgw0 ceph --cluster={cluster} -n client.rgw.{hostname}.rgw0 --connect-timeout 5 --keyring /var/lib/ceph/radosgw/{cluster}-rgw.{hostname}.rgw0/keyring osd pool get {pool_name} size".format(  # noqa E501
                hostname=hostname,
                cluster=cluster,
                pool_name=pool_name,
                container_binary=container_binary
            ))
            assert cmd.rc == 0
