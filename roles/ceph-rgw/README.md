# Ansible role: Ceph Rados Gateway

This role bootstraps Ceph Rados Gateway(s).
It can bootstrap dockerized Ceph Rados Gateway(s).

It supports two methods to configure Rados Gateway:

* with civetweb (default and preferred)
* with Apache and CGI

It can be configured to support a connection with OpenStack Keystone.

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
     - { role: leseb.ceph-rgw }
```

# Contribution

**THIS REPOSITORY DOES NOT ACCEPT PULL REQUESTS**
**PULL REQUESTS MUST GO THROUGH [CEPH-ANSIBLE](https://github.com/ceph/ceph-ansible)**

# License

Apache

# Author Information

This role was created by [Sébastien Han](http://sebastien-han.fr/).
