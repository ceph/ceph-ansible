ceph-ansible stable-4.0 release note
====================================

Ansible version support
-----------------------

This version supports Ansible 2.8

Ceph version support
--------------------

This version can deploy Ceph Nautilus.
Note that the general intent for Ceph Ansible is to support one Ceph release only.
The next version will support Octopus, then the one after that will support Pacific Ceph release.

Added features
----------------

* Add python 3 support.
* Add podman support.
* Add RHEL 8 and openSUSE Leap 15 support.
* Add RHCS 4 support.
* Add Ceph Dashboard integration (old ceph-metrics).
* Add support for scaling up/down the Ceph daemons.
* Add a playbook for filestore to bluestore migration.
* Add a playbook for docker to podman migration.
* Add PG autoscaler support.
* Add support for replacing a mon.
* Add radosgw multiple instances on the same host support.
* Add multiple radosgw realm/zonegroup/zone support.
* Add radosgw beast frontend support.
* Shrink OSD with osd_fsid via ceph-volume.
* Support OSD scaling up using main playbook with --limit.
* Support internal nfs-ganesha deployment with external ceph cluster support.
* Add wal_devices, block_db_devices options support to ceph_volume module.
* Add RBD mirror configuration on containerized deployment and also configure the mirror pool.
* Add container registry authentication support.
* Add device class support in crush rules.

Removed features
----------------

* Remove openSUSE Leap 42 support.
* Remove Debian support from RHCS deployment.
* Remove ceph-common-coreos and ceph-agent roles.
* Remove KV store support.
* Remove infrastructure-playbooks/rgw-standalone.yml
* Remove Luminous and Mimic support.
* Remove ceph-disk support.
* Remove notario validation.
* Remove fetch_directory dependency.
* Remove ceph aliases for containerized deployment.

Deprecation warnings and incoming removal
-----------------------------------------
* Drop add-osd.yml playbook, it will be replaced by main playbook with --limit option.
* Ceph Ansible doesn’t configure ISCSI gateways anymore. This should be done manually or via the Ceph Dashboard UI.
* site-docker.yml.sample, purge-docker-cluster.yml symlinks will be removed.

Major changes from stable-3.2
-----------------------------

* Updating the Ceph ISCSI major version from 2.x to 3.x.
* Beast is the default radosgw frontend instead of Civetweb.
* Due to ceph-disk removal then there’s no collocated and non-collocated OSD scenarios anymore. The default scenario is always lvm (ceph-volume) which can be used with or without the batch mode.

Notable changes from stable-3.2
-------------------------------

* Updating the NFS Ganesha minor version from V2.7 to V2.8.
* The ceph-docker role has been split into two different roles: ceph-container-engine and ceph-container-common.
