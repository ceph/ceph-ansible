ceph-ansible stable-7.0 release note
====================================

Ansible version support
-----------------------

This version supports ansible-core 2.12

Ceph version support
--------------------

This version can deploy Ceph Quincy.
Note that the general intent for Ceph Ansible is to support one Ceph release only.
The next version will support Reef, then the one after that will support S Ceph release.

Added features
----------------

* Add RHCS 6 support.

Removed features
----------------

Deprecation warnings and incoming removal
-----------------------------------------

The next release of ceph-ansible (`stable-8.0`) will be released with some non-backward compatible changes:

* `ceph/daemon` images support will be removed (use the ceph/ceph container image instead).
* some parts of the existing roles will be moved to dedicated playbooks (eg: osd: openstack_config.yml, rgw: multisite.yml, ...)

NOTE: rgw multisite deployments might be unstable with `stable-8.0`

Major changes from stable-6.0
-----------------------------

* rbd-mirror: major refactor

Notable changes from stable-6.0
-------------------------------

* ipwrap has moved to ansible.utils
* Add --security-opt label=disable to all containers
