ceph-ansible
============

Ansible playbook for Ceph!

## What does it do?

General support for:

* Monitors
* OSDs
* MDSs
* RGW

More details:

* Authentication (cephx), this can be disabled.
* Supports cluster public and private network.
* Monitors deployment. You can easily start with one monitor and then progressively add new nodes. So can deploy one monitor for testing purpose. For production, I recommend to a
* Object Storage Daemons. Like the monitors you can start with a certain amount of nodes and then grow this number. The playbook either supports a dedicated device for storing th
* Metadata daemons.
* Collocation. The playbook supports collocating Monitors, OSDs and MDSs on the same machine.
* The playbook was validated on Debian Wheezy, Ubuntu 12.04 LTS and CentOS 6.4.
* Tested on Ceph Dumpling and Emperor.
* A rolling upgrade playbook was written, an upgrade from Dumpling to Emperor was performed and worked.


## Setup with Vagrant

First source the `rc` file:

    $ source rc

Edit your `/etc/hosts` file with:

    # Ansible hosts
    127.0.0.1   ceph-mon0
    127.0.0.1   ceph-mon1
    127.0.0.1   ceph-mon2
    127.0.0.1   ceph-osd0
    127.0.0.1   ceph-osd1
    127.0.0.1   ceph-osd2
    127.0.0.1   ceph-rgw

**Now since we use Vagrant and port forwarding, don't forget to collect the SSH local port of your VMs.**
Then edit your `hosts` file accordingly.

Ok let's get serious now.
Run your virtual machines:

```bash
$ vagrant up
...
...
...
```

Test if Ansible can access the virtual machines:

```bash
$ ansible all -m ping
ceph-mon0 | success >> {
    "changed": false,
    "ping": "pong"
}

ceph-mon1 | success >> {
    "changed": false,
    "ping": "pong"
}

ceph-osd0 | success >> {
    "changed": false,
    "ping": "pong"
}

ceph-osd2 | success >> {
    "changed": false,
    "ping": "pong"
}

ceph-mon2 | success >> {
    "changed": false,
    "ping": "pong"
}

ceph-osd1 | success >> {
    "changed": false,
    "ping": "pong"
}

ceph-rgw | success >> {
    "changed": false,
    "ping": "pong"
}
```

**DON'T FORGET TO GENERATE A FSID FOR THE CLUSTER AND A KEY FOR THE MONITOR**

For this go to `group_vars/all` and `group_vars/mons` and append the fsid and key.

These are **ONLY** examples, **DON'T USE THEM IN PRODUCTION**:

* fsid: 4a158d27-f750-41d5-9e7f-26ce4c9d2d45
* monitor: AQAWqilTCDh7CBAAawXt6kyTgLFCxSvJhTEmuw==

Ready to deploy? Let's go!

```bash
$ ansible-playbook -f 7 -v site.yml
...
...
 ____________
< PLAY RECAP >
 ------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||


ceph-mon0                  : ok=13   changed=10   unreachable=0    failed=0
ceph-mon1                  : ok=13   changed=9    unreachable=0    failed=0
ceph-mon2                  : ok=13   changed=9    unreachable=0    failed=0
ceph-osd0                  : ok=19   changed=12   unreachable=0    failed=0
ceph-osd1                  : ok=19   changed=12   unreachable=0    failed=0
ceph-osd2                  : ok=19   changed=12   unreachable=0    failed=0
ceph-rgw                   : ok=23   changed=16   unreachable=0    failed=0
```

Check the status:

```bash
$ vagrant ssh mon0 -c "sudo ceph -s"
    cluster 4a158d27-f750-41d5-9e7f-26ce4c9d2d45
     health HEALTH_OK
     monmap e3: 3 mons at {ceph-mon0=192.168.0.10:6789/0,ceph-mon1=192.168.0.11:6789/0,ceph-mon2=192.168.0.12:6789/0}, election epoch 6, quorum 0,1,2 ceph-mon0,ceph-mon1,ceph-mon
     mdsmap e6: 1/1/1 up {0=ceph-osd0=up:active}, 2 up:standby
     osdmap e10: 6 osds: 6 up, 6 in
      pgmap v17: 192 pgs, 3 pools, 9470 bytes data, 21 objects
            205 MB used, 29728 MB / 29933 MB avail
                 192 active+clean
