import pytest
import json


class TestRGWs(object):

    @pytest.mark.no_docker
    def test_rgw_bucket_default_quota_is_set(self, node, host):
        assert host.file(node["conf_path"]).contains("rgw override bucket index max shards")
        assert host.file(node["conf_path"]).contains("rgw bucket default quota max objects")

    @pytest.mark.no_docker
    def test_rgw_bucket_default_quota_is_applied(self, node, host):
        radosgw_admin_cmd = "sudo radosgw-admin --cluster={} user create --uid=test --display-name Test".format(node["cluster_name"])
        radosgw_admin_output = host.check_output(radosgw_admin_cmd)
        radosgw_admin_output_json = json.loads(radosgw_admin_output)
        assert radosgw_admin_output_json["bucket_quota"]["enabled"] == True
        assert radosgw_admin_output_json["bucket_quota"]["max_objects"] == 1638400

    @pytest.mark.no_docker
    def test_rgw_tuning_pools_are_set(self, node, host):
        cmd = "sudo ceph --cluster={} --connect-timeout 5 osd dump".format(node["cluster_name"])
        output = host.check_output(cmd)
        pools = node["vars"]["create_pools"]
        for pool_name, pg_num in pools.items():
            assert pool_name in output
            pg_num_str = "pg_num {pg_num}".format(pg_num=pg_num["pg_num"])
            assert pg_num_str in output
