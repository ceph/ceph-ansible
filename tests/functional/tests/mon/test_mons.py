import pytest


class TestMons(object):

    @pytest.mark.no_docker
    def test_ceph_mon_package_is_installed(self, node, host):
        assert host.package("ceph-mon").is_installed

    @pytest.mark.parametrize("mon_port", [3300, 6789])
    def test_mon_listens(self, node, host, setup, mon_port):
        assert host.socket("tcp://{address}:{port}".format(
            address=setup["address"],
            port=mon_port
        )).is_listening

    def test_mon_service_enabled_and_running(self, node, host):
        service_name = "ceph-mon@{hostname}".format(
            hostname=node["vars"]["inventory_hostname"]
        )
        s = host.service(service_name)
        assert s.is_enabled
        assert s.is_running

    @pytest.mark.no_docker
    def test_can_get_cluster_health(self, node, host, setup):
        cmd = "sudo ceph --cluster={} --connect-timeout 5 -s".format(setup["cluster_name"])  # noqa E501
        output = host.check_output(cmd)
        assert output.strip().startswith("cluster")
