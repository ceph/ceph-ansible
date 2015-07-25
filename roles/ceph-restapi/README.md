# Ansible role: Ceph REST API

This role bootstraps Ceph REST API(s).
It can bootstrap dockerized Ceph REST API(s).

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
     - { role: leseb.ceph-restapi }
```

# License

Apache

# Author Information

This role was created by [Sébastien Han](http://sebastien-han.fr/).
