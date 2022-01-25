import os
import sys
from mock.mock import patch, MagicMock
import pytest

sys.path.append("./library")
import radosgw_caps  # noqa: E402


fake_binary = "radosgw-admin"
fake_cluster = "ceph"
fake_container_binary = "podman"
fake_container_image = "docker.io/ceph/daemon:latest"
fake_container_cmd = [
    fake_container_binary,
    "run",
    "--rm",
    "--net=host",
    "-v",
    "/etc/ceph:/etc/ceph:z",
    "-v",
    "/var/lib/ceph/:/var/lib/ceph/:z",
    "-v",
    "/var/log/ceph/:/var/log/ceph/:z",
    "--entrypoint=" + fake_binary,
    fake_container_image,
]
fake_user = "foo"
fake_caps = ["users=write", "zone=*", "metadata=read,write"]
fake_params = {
    "cluster": fake_cluster,
    "name": fake_user,
    "caps": fake_caps,
}


class TestRadosgwCapsModule(object):
    @patch.dict(os.environ, {"CEPH_CONTAINER_BINARY": fake_container_binary})
    def test_container_exec(self):
        cmd = radosgw_caps.container_exec(fake_binary, fake_container_image)
        assert cmd == fake_container_cmd

    def test_not_is_containerized(self):
        assert radosgw_caps.is_containerized() is None

    @patch.dict(os.environ, {"CEPH_CONTAINER_IMAGE": fake_container_image})
    def test_is_containerized(self):
        assert radosgw_caps.is_containerized() == fake_container_image

    @pytest.mark.parametrize("image", [None, fake_container_image])
    @patch.dict(os.environ, {"CEPH_CONTAINER_BINARY": fake_container_binary})
    def test_pre_generate_radosgw_cmd(self, image):
        if image:
            expected_cmd = fake_container_cmd
        else:
            expected_cmd = [fake_binary]

        assert radosgw_caps.pre_generate_radosgw_cmd(image) == expected_cmd

    @pytest.mark.parametrize("image", [None, fake_container_image])
    @patch.dict(os.environ, {"CEPH_CONTAINER_BINARY": fake_container_binary})
    def test_generate_radosgw_cmd(self, image):
        if image:
            expected_cmd = fake_container_cmd
        else:
            expected_cmd = [fake_binary]

        expected_cmd.extend(["--cluster", fake_cluster, "caps"])
        assert (
            radosgw_caps.generate_radosgw_cmd(fake_cluster, [], image) == expected_cmd
        )

    def test_add_caps(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            "--cluster",
            fake_cluster,
            "caps",
            "add",
            "--uid=" + fake_user,
            "--caps=" + ";".join(fake_caps),
        ]

        assert radosgw_caps.add_caps(fake_module) == expected_cmd

    def test_remove_caps(self):
        fake_module = MagicMock()
        fake_module.params = fake_params
        expected_cmd = [
            fake_binary,
            "--cluster",
            fake_cluster,
            "caps",
            "rm",
            "--uid=" + fake_user,
            "--caps=" + ";".join(fake_caps),
        ]

        assert radosgw_caps.remove_caps(fake_module) == expected_cmd
