# Ansible role: Ceph Metadata

This role bootstraps Ceph metadata(s).
It can bootstrap dockerized Ceph metadata(s).

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
     - { role: leseb.ceph-mds }
```

# License

Apache

# Author Information

This role was created by [Sébastien Han](http://sebastien-han.fr/).
