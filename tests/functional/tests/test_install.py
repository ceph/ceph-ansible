import os


class TestInstall(object):

    def test_ceph_dir_exists(self):
        assert os.path.isdir('/etc/ceph')

    def test_ceph_conf_exists(self):
        assert os.path.isfile('/etc/ceph/ceph.conf')
