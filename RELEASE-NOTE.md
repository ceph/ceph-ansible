ceph-ansible stable-5.0 release note
====================================

Ansible version support
-----------------------

This version supports Ansible 2.9

Ceph version support
--------------------

This version can deploy Ceph Octopus.
Note that the general intent for Ceph Ansible is to support one Ceph release only.
The next version will support Pacific, then the one after that will support Q Ceph release.

Added features
----------------

* Add full CentOS 8 support.
* Add RHCS 5 support.

Removed features
----------------

* Remove CentOS 7 support for non containerized deployment with dashboard enabled.

Deprecation warnings and incoming removal
-----------------------------------------


Major changes from stable-4.0
-----------------------------

* Updating the NFS Ganesha release from V2.8 to V3.2.
* site-docker.yml and purge-docker-cluster.yml symlinks have been removed.

Notable changes from stable-4.0
-------------------------------

* Containers aren’t using the ulimit parameter for configuring the nofile value.
* Add ceph_pool module for managing pool operations.
