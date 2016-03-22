# Ansible role: Ceph Storage Agent

This role installs python and pip on CoreOS.

# Requirements

This role has to be run without gathering facts and with sudo attribute.

# Role variables

Have a look at: `defaults/main.yml`.

## Mandatory variables

None.

# Dependencies

New CoreOS releases support pypy in version 2.4 and above. Unfortunetly CoreOS stable channel
has to be used with pypy in version 2.4 and below due to some dependency issues.

# Example Playbook

```
- hosts: servers
  remote_user: core
  become: True
  gather_facts: false
  roles:
     - { role: ceph-common-coreos }
```

# Contribution

**THIS REPOSITORY DOES NOT ACCEPT PULL REQUESTS**
**PULL REQUESTS MUST GO THROUGH [CEPH-ANSIBLE](https://github.com/ceph/ceph-ansible)**

# License

Apache

# Author Information

This role was created by Piotr Prokop.
