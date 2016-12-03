
class TestInstall(object):

    def test_ceph_dir_exists(self, File):
        assert File('/etc/ceph').exists

    def test_ceph_dir_is_a_directory(self, File):
        assert File('/etc/ceph').is_directory

    def test_ceph_conf_exists(self, File):
        assert File('/etc/ceph/ceph.conf').exists

    def test_ceph_conf_is_a_file(self, File):
        assert File('/etc/ceph/ceph.conf').is_file

    def test_ceph_command_exists(self, Command):
        assert Command.exists("ceph")
