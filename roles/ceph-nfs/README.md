# Ansible role: Ceph NFS Gateway

This role bootstraps Ceph NFS Gateway(s).
It can bootstrap dockerized Ceph NFS Gateway(s).  NFS support is provided by
the NFS Ganesha project.

It can provide one or both of NFS File access (requires at least one ceph-mds
role) or NFS Object access (requires at least one ceph-rgw role).

# Requirements

Nothing, it runs out of the box.

# Role variables

Have a look at: `defaults/main.yml`.

## Mandatory variables

None.

# Dependencies

The role `ceph.ceph-common` must be installed.

# Example Playbook

```
- hosts: servers
  remote_user: ubuntu
  roles:
     - { role: ceph.ceph-nfs }
```

# Contribution

**THIS REPOSITORY DOES NOT ACCEPT PULL REQUESTS**
**PULL REQUESTS MUST GO THROUGH [CEPH-ANSIBLE](https://github.com/ceph/ceph-ansible)**

# License

Apache

# Author Information

This role was created by [Daniel Gryniewicz](http://redhat.com/).
