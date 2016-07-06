# Ansible role: Ceph Common

This role does several things prior to bootstrapping your Ceph cluster:

* Checks the system and validates that Ceph can be installed
* Tunes the operating system if the node is an OSD server
* Installs Ceph
* Generates `ceph.conf`

# Requirements

Move the `plugins/actions/config_template.py` file to your top level playbook directory.
Edit your `ansible.cfg` like so:

    action_plugins = plugins/actions

Depending on how you are managing your playbook, the path might be different so edit the file accordingly if necessary.

# Role variables

Have a look at `defaults/main.yml`.

## Mandatory variables

* Install source, choose one of these:
  * `ceph_stable`
  * `ceph_dev`
  * `ceph_stable_ice`
  * `ceph_stable_rh_storage`
  * `ceph_custom`
* `journal_size`
* `monitor_interface`
* `public_network`
* `cluster_network`

## Handlers

* update apt cache
* restart ceph-mon
* restart ceph-osd
* restart ceph-mds
* restart ceph-rgw
* restart ceph-restapi
* restart apache2

# Dependencies

None

# Example Playbook

```
- hosts: servers
  remote_user: ubuntu
  roles:
     - { role: leseb.ceph-common }
```

# Misc

This role is a **mandatory** dependency for the following roles:

* ceph-mon
* ceph-osd
* ceph-mds
* ceph-rgw
* ceph-restapi

# Contribution

**THIS REPOSITORY DOES NOT ACCEPT PULL REQUESTS**.
**PULL REQUESTS MUST GO THROUGH [CEPH-ANSIBLE](https://github.com/ceph/ceph-ansible)**.

# License

Apache

# Author Information

This role was created by [Sébastien Han](http://sebastien-han.fr/).
