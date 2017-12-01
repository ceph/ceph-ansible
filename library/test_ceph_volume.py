from . import ceph_volume


class TestCephVolumeModule(object):

    def test_data_no_vg(self):
        result = ceph_volume.get_data("/dev/sda", None)
        assert result == "/dev/sda"

    def test_data_with_vg(self):
        result = ceph_volume.get_data("data-lv", "data-vg")
        assert result == "data-vg/data-lv"

    def test_journal_no_vg(self):
        result = ceph_volume.get_journal("/dev/sda1", None)
        assert result == "/dev/sda1"

    def test_journal_with_vg(self):
        result = ceph_volume.get_journal("journal-lv", "journal-vg")
        assert result == "journal-vg/journal-lv"

    def test_db_no_vg(self):
        result = ceph_volume.get_db("/dev/sda1", None)
        assert result == "/dev/sda1"

    def test_db_with_vg(self):
        result = ceph_volume.get_db("db-lv", "db-vg")
        assert result == "db-vg/db-lv"

    def test_wal_no_vg(self):
        result = ceph_volume.get_wal("/dev/sda1", None)
        assert result == "/dev/sda1"

    def test_wal_with_vg(self):
        result = ceph_volume.get_wal("wal-lv", "wal-vg")
        assert result == "wal-vg/wal-lv"
