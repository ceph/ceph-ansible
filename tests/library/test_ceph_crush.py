import sys
sys.path.append('./library')
import ceph_crush
import pytest


class TestCephCrushModule(object):

    def test_no_host(self):
        location = [
            ("chassis", "monchassis"),
            ("rack", "monrack"),
            ("row", "marow"),
            ("pdu", "monpdu"),
            ("pod", "monpod"),
            ("room", "maroom"),
            ("datacenter", "mondc"),
            ("region", "maregion"),
            ("root", "maroute"),
        ]
        with pytest.raises(Exception):
            result = ceph_crush.sort_osd_crush_location(location, None)

    def test_lower_than_two_bucket(self):
        location = [
            ("chassis", "monchassis"),
        ]
        with pytest.raises(Exception):
            result = ceph_crush.sort_osd_crush_location(location, None)

    def test_invalid_bucket_type(self):
        location = [
            ("host", "monhost"),
            ("chassis", "monchassis"),
            ("rackyyyyy", "monrack"),
        ]
        with pytest.raises(Exception):
            result = ceph_crush.sort_osd_crush_location(location, None)

    def test_ordering(self):
        expected_result = [
            ("host", "monhost"),
            ("chassis", "monchassis"),
            ("rack", "monrack"),
            ("row", "marow"),
            ("pdu", "monpdu"),
            ("pod", "monpod"),
            ("room", "maroom"),
            ("datacenter", "mondc"),
            ("region", "maregion"),
            ("root", "maroute"),
        ]
        expected_result_reverse = expected_result[::-1]
        result = ceph_crush.sort_osd_crush_location(expected_result_reverse, None)
        assert expected_result == result

    def test_generate_commands(self):
        cluster = "test"
        expected_command_list = [
            ['ceph', '--cluster', cluster, 'osd', 'crush', "add-bucket", "monhost", "host"],
            ['ceph', '--cluster', cluster, 'osd', 'crush', "add-bucket", "monchassis", "chassis"],
            ['ceph', '--cluster', cluster, 'osd', 'crush', "move", "monhost", "chassis=monchassis"],
            ['ceph', '--cluster', cluster, 'osd', 'crush', "add-bucket", "monrack", "rack"],
            ['ceph', '--cluster', cluster, 'osd', 'crush', "move", "monchassis", "rack=monrack"],
        ]

        location = [
            ("host", "monhost"),
            ("chassis", "monchassis"),
            ("rack", "monrack"),
        ]
        result = ceph_crush.create_and_move_buckets_list(cluster, location)
        assert result == expected_command_list

    def test_generate_commands_container(self):
        cluster = "test"
        containerized = "docker exec -ti ceph-mon"
        expected_command_list = [
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph', '--cluster', cluster, 'osd', 'crush', "add-bucket", "monhost", "host"],
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph', '--cluster', cluster, 'osd', 'crush', "add-bucket", "monchassis", "chassis"],
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph', '--cluster', cluster, 'osd', 'crush', "move", "monhost", "chassis=monchassis"],
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph', '--cluster', cluster, 'osd', 'crush', "add-bucket", "monrack", "rack"],
            ['docker', 'exec', '-ti', 'ceph-mon', 'ceph', '--cluster', cluster, 'osd', 'crush', "move", "monchassis", "rack=monrack"],
        ]

        location = [
            ("host", "monhost"),
            ("chassis", "monchassis"),
            ("rack", "monrack"),
        ]
        result = ceph_crush.create_and_move_buckets_list(cluster, location, containerized)
        assert result == expected_command_list
