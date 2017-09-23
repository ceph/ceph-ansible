# Ansible role: Ceph config

This role does several things:

* Create the cluster fsid
* Generate the `ceph.conf` file

# Requirements

Nothing, it runs out of the box.

# Role variables

Have a look at `defaults/main.yml`.

## Mandatory variables

None.

# Dependencies

None

# Example Playbook

```
- hosts: servers
  remote_user: ubuntu
  roles:
     - { role: ceph.ceph-config }
```

# Contribution

**THIS REPOSITORY DOES NOT ACCEPT PULL REQUESTS**.
**PULL REQUESTS MUST GO THROUGH [CEPH-ANSIBLE](https://github.com/ceph/ceph-ansible)**.

# License

Apache

# Author Information

This role was created by Guillaume Abrioux.
