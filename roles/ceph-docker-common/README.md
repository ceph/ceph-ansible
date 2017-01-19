# Ansible role: Ceph Docker Common 

This role contains variables and tasks common to
all containerized deployments.

# Requirements

Nothing, it runs out of the box.

# Role variables

Have a look at: `defaults/main.yml`.

## Mandatory variables

None.

# Dependencies

None.

# Example Playbook

```
- hosts: mons 
  roles:
     - { role: ceph.ceph-docker-common }
```

# Misc

This role is a **mandatory** dependency for the following roles
if you are doing a containerized deployment:

* ceph-mon
* ceph-osd
* ceph-mds
* ceph-rgw
* ceph-restapi

# Contribution

**THIS REPOSITORY DOES NOT ACCEPT PULL REQUESTS**
**PULL REQUESTS MUST GO THROUGH [CEPH-ANSIBLE](https://github.com/ceph/ceph-ansible)**

# License

Apache

# Author Information

This role was created by Andrew Schoen.
