# Ansible role: Ceph OSD

This role bootstraps Ceph OSD(s).
It can bootstrap dockerized Ceph OSD(s).

# Requirements

Nothing, it runs out of the box.

# Role variables

Have a look at: `defaults/main.yml`.

## Mandatory variables

Choose between the following scenario to configure your OSDs, **choose only one**:

* `journal_collocation`
* `raw_multi_journal`

Then:

* `devices`
* `raw_journal_devices` (**only if** you activated `raw_multi_journal`)

# Dependencies

The role `leseb.ceph-common` must be installed.

# Example Playbook

```
- hosts: servers
  remote_user: ubuntu
  roles:
     - { role: leseb.ceph-osd }
```

# Contribution

**THIS REPOSITORY DOES NOT ACCEPT PULL REQUESTS**
**PULL REQUESTS MUST GO THROUGH [CEPH-ANSIBLE](https://github.com/ceph/ceph-ansible)**

# License

Apache

# Author Information

This role was created by [Sébastien Han](http://sebastien-han.fr/).
