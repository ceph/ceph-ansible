# Ansible role: Ceph Monitor

This role mainly bootstraps Ceph monitor(s) but also has several capabilities:

* Deploys Ceph monitor(s)
* Manages Ceph keys
* Can create OpenStack pools, users and keys
* Secures a cluster (protect pools)
* Bootstraps dockerized Ceph monitors

# Requirements

Nothing, it runs out of the box.

# Role variables

Have a look at: `defaults/main.yml`.

## Mandatory variables

None.

# Dependencies

The role `leseb.ceph-common` must be installed.

# Example Playbook

```
- hosts: servers
  remote_user: ubuntu
  roles:
     - { role: leseb.ceph-mon }
```

# License

Apache

# Author Information

This role was created by [Sébastien Han](http://sebastien-han.fr/).
