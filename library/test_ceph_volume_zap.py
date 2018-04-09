from . import ceph_volume_zap


class TestCephVolumeZapModule(object):

    def test_device_no_vg(self):
        result = ceph_volume_zap.get_device("/dev/sda", None)
        assert result == "/dev/sda"

    def test_device_with_vg(self):
        result = ceph_volume_zap.get_device("data-lv", "data-vg")
        assert result == "data-vg/data-lv"
