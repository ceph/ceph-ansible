# Ansible role: Ceph Fetch Keys 

This role connects to mons and fetches all of keys into
the local ``fetch_directory``.

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
     - { role: leseb.ceph-fetch-keys }
```

# Contribution

**THIS REPOSITORY DOES NOT ACCEPT PULL REQUESTS**
**PULL REQUESTS MUST GO THROUGH [CEPH-ANSIBLE](https://github.com/ceph/ceph-ansible)**

# License

Apache

# Author Information

This role was created by Andrew Schoen.
