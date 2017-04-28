import pytest


class TestRGWs(object):

    def test_rgw_bucket_default_quota_is_set(self, node, File):
        assert File(node["conf_path"]).contains("rgw override bucket index max shards")
        assert File(node["conf_path"]).contains("rgw bucket default quota max objects")

    @pytest.mark.no_docker
    def test_rgw_tuning_pools_are_set(self, node, Command):
        cmd = "sudo ceph --cluster={} --connect-timeout 5 osd dump".format(node["cluster_name"])
        output = Command.check_output(cmd)
        pools = node["vars"]["create_pools"]
        for pool_name, pg_num in pools.items():
            assert pool_name in output
            pg_num_str = "pg_num {pg_num}".format(pg_num = pg_num["pg_num"])
            assert pg_num_str in output
