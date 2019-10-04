RGW Multisite
=============

This document contains directions for configuring RGW Multisite in ceph-ansible for multiple realms or multiple zonegroups or multiple zones on a cluster.

Multisite replication can be configured either over multiple Ceph clusters or in a single Ceph cluster using Ceph version **Jewel or newer**.

The first two sections give an overview on working with ansible inventory and the variables to configure RGW Multisite.

The next sections are instructions on deploying a single Ceph cluster with multiple realms

For information on configuring RGW Multisite with just one realms, zone groups, and zone in a cluster, refer to [README-MULTISITE.md](README-MULTISITE.md).

# Working with Ansible Inventory

If you are familiar with basic ansible terminology, working with inventory files, and inventory groups, feel free to skip this section.

## The Inventory File

Ceph-ansible starts up all the different daemons in a Ceph cluster.

Each daemon (osd.0, mon.1, rgw.a) is given a line in the inventory file. Each line is called a **host** in ansible.
Each type of daemon (OSD, Mon, RGW, Mgr, etc.) is given a **group** with its respective daemons in the ansible inventory file.

Here is an example of an inventory file (in .ini format) for a Ceph cluster with 1 Mgrs, 4 RGWs, 3 OSDs, and 2 Mons:
```
[mgrs]
	mgr-000 ansible_ssh_host=192.168.224.48 ansible_ssh_port=22
[rgws]
	rgws-000 ansible_ssh_host=192.168.216.145 ansible_ssh_port=22 radosgw_address=192.168.216.145
	rgws-001 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.215.178
	rgws-002 ansible_ssh_host=192.168.132.221 ansible_ssh_port=22 radosgw_address=192.168.132.221
	rgws-003 ansible_ssh_host=192.168.145.7 ansible_ssh_port=22 radosgw_address=192.168.145.7
[osds]
	osd-002 ansible_ssh_host=192.168.176.118 ansible_ssh_port=22
	osd-001 ansible_ssh_host=192.168.226.21 ansible_ssh_port=22
	osd-000 ansible_ssh_host=192.168.230.196 ansible_ssh_port=22
[mons]
	mon-000 ansible_ssh_host=192.168.210.155 ansible_ssh_port=22 monitor_address=192.168.210.155
	mon-001 ansible_ssh_host=192.168.179.111 ansible_ssh_port=22 monitor_address=192.168.179.111
```

Notice there are 4 groups defined here: mgrs, rgws, osds, mons.

There is one host (mgr-000) in mgrs, 4 hosts (rgws-000, rgws-001, rgws-002, rgws-003) in rgws, 3 hosts (osd-000, osd-001, osd-002) in osds, and 2 hosts (mon-000, mon-001) in mons.

## The Groups of Inventory Groups

Groups in the inventory can have subgroups. Consider the following inventory file:
```
[rgws]

[rgws:children]
usa
canada

[usa]
	rgws-000 ansible_ssh_host=192.168.216.145 ansible_ssh_port=22 radosgw_address=192.168.216.145
	rgws-001 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.215.178

[canada]
	rgws-002 ansible_ssh_host=192.168.132.221 ansible_ssh_port=22 radosgw_address=192.168.132.221
	rgws-003 ansible_ssh_host=192.168.145.7 ansible_ssh_port=22 radosgw_address=192.168.145.7
```

In this inventory rgws-000 and rgws-001 are in group `usa` and rgws-002 and rgws-003 are in group `canada`.

`usa` and `canada` are both child groups of `rgws`. Groups that are children can have children groups of their own.

## group_vars

In the ceph-ansible tree there is a directory called `group_vars`. This directory has a collection of .yml files for variables set for each of the groups.

The variables defined in `all.yml` apply to all groups in the inventory.
When a variable, for example if `rgw_realm: usa`, is set in `group_vars/usa.yml`, `milkway` will be the value for `rgw_realm` for all of the RGW hosts in group `milkway`.

If a group is a child of another group, the hosts in that group inherit all the parent specific values.
If a variable is set in a group and its parent group, the variables evaluates to the value of the group closest to where the host is defined.

For example if in the above inventory configuration `rgw_realm: nowhere` in `group_vars/rgws.yml` and `rgw_realm: usa` in `group_vars/usa.yml`, then the value for `rgw_realm` will be `usa` for rgws-000 and rgws-001.

For more information on working with ansible inventory please visit: https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html

# RGW Multisite Config Overview

## Inventory Groups for Multisite

To run multisite, the inventory files needs to have a group for `rgws`, groups for `realms`, and groups for `zones`.

Each of the groups that is a `realm` needs to be a child of the `rgws` group.
Each of the groups that is a `zone` needs to be a child of one the groups that is a `realm`.

Each RGW host in the inventory must be in one of the groups that is a zone. Each RGW host can only be in one zone at a time.

Consider the following inventory file:
```
[rgws]

[rgws:children]
usa
canada

[usa]
[usa:children]
boston
seattle

[boston]
	rgws-000 ansible_ssh_host=192.168.216.145 ansible_ssh_port=22 radosgw_address=192.168.216.145
[seattle]
	rgws-001 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.215.178

[canada]
[canada:children]
toronto

[toronto]
	rgws-002 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.215.199
	rgws-003 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.194.109
```

In this inventory there are 2 realms: `usa` and `canada`.

The realm `usa` has 2 zones: `boston` and `seattle`. Zone `boston` contains the RGW on host rgw-000. Zone `seattle` contains the RGW on host rgw-001.

The realm `canada` only has 1 zone `toronto`. Zone `toronto` contains the RGWs on the hosts rgws-002 and rgws-003.

Finally, `radosgw-address` must be set for all rgw hosts.

## Multisite Variables in group_vars/all.yml

The following are the multisite variables that can be configured for all RGW hosts via `group_vars/all.yml` set to their defaults:
```
## Rados Gateway options
#
radosgw_num_instances: 1

#############
# MULTISITE #
#############

rgw_multisite: false
rgw_zone: default
```

The **only** value that needs to be changed is `rgw_multisite`. Changing this variable to `true` runs the multisite playbooks in ceph-ansible on all the RGW hosts.

`rgw_zone` is set to "default" to enable compression for clusters configured without RGW multi-site.
Changing this value in a zone specific .yaml file overrides this default value.

`radosgw_num_instances` must be set to 1. The playbooks do not support deploying RGW Multisite on hosts with more than 1 RGW.

## Multisite Variables in group_vars/{zone name}.yml
Each of the zones in a multisite deployment must have a .yml file in `group_vars/` with its name.

All values must be set in a zone's configuation file.

In the example inventory configuration, `group_vars/` would have files for zones named `boston.yml`, `seattle.yml` and `toronto.yml`.

The variables in a zone specific file must be the same as the below variables in `group_vars/zone.yml.sample`:
```
rgw_zone: boston

rgw_zonemaster: true
rgw_zonesecondary: false

rgw_zonegroup: solarsystem

rgw_zonegroupmaster: true
```
A group of 1 or more RGWs can be grouped into a **zone**.

To avoid any confusion the value of `rgw_zone` should always be set to the name of the file it is in. For example this file should be named `group_vars/boston.yml`

`rgw_zonemaster` specifies that the zone will be the master zone in a zonegroup.

`rgw_zonesecondary` specifies that the zone will be a secondary zone in a zonegroup.

Both `rgw_zonemaster` and `rgw_zonesecondary` need to be defined. They cannot have the same value.

A zone is default if it is the only zone in a cluster.
The ceph-ansible multisites playbooks automatically make a zone default if it is the only zone in a cluster.

A group of 1 or more zones can be grouped into a **zonegroup**.

A zonegroup must have a master zone in order for secondary zones to exist in it.

Setting `rgw_zonegroupmaster: true` specifies the zonegroup will be the master zonegroup in a realm.

Setting `rgw_zonegroupmaster: false` indicates the zonegroup will be non-master.

There must be one master zonegroup per realm. After the master zonegroup is created there can be any number of non-master zonegroups per realm.

A zonegroup is default if it is the only zonegroup in a cluster.
The ceph-ansible multisite playbooks automatically make a zonegroup default if it is the only zonegroup in a cluster.

## Multisite Variables in group_vars/{realm name}.yml

Each of the realms in a multisite deployment must have a .yml file in `group_vars/` with its name.

All values must be set in a realm's configuation file.

In the example inventory configuration, `group_vars/` would have files named `usa.yml` and `canada.yml`.

The variables in a realm specific file must be the same below variables in `group_vars/realm.yml.sample`:
```
rgw_realm: usa

system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt

rgw_zone_user: bostonian
rgw_zone_user_display_name: "Mark Wahlberg"

rgw_pull_port: "{{ radosgw_frontend_port }}"
rgw_pull_proto: "http"
rgw_pullhost: localhost
```
To avoid any confusion the value of `rgw_realm` should always be set to the name of the file it is in. For example this file should be `group_vars/usa.yml`

The `system_access_key` and `system_secret_key` should be user generate and different for each realm.

Each realm has a system user that is created, with a display name for it.

The variables `rgw_pull_port`, `rgw_pull_proto`, `rgw_pullhost`, are joined together to make an endpoint string needed to create secondary zones.

This endpoint is of one of the RGW endpoints in a master zone in the zonegroup and realm you want to create secondary zones in.

This endpoint **must be resolvable** from the mons and rgws in the cluster the secondary zone(s)  are being created in.

# Deployment Scenario #1: Single Realm & Zonegroup with Multiple Ceph Clusters

## Creating the Master Zone in the Primary Cluster

This deployment will setup a default realm, default master zonegroup and default master zone in the Ceph cluster.

The following inventory file will be used for the primary cluster:
```
[rgws]

[rgws:children]
usa

[usa]
[usa:children]
boston

[boston]
	rgws-000 ansible_ssh_host=192.168.216.145 ansible_ssh_port=22 radosgw_address=192.168.216.145
```

1. Generate System Access and System Secret Keys for the Realm "usa"

```
echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > usa-multi-site-keys.txt
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> usa-multi-site-keys.txt
```
2. Edit `group_vars/all.yml` for the Primary cluster

```
## Rados Gateway options
#
radosgw_num_instances: 1

#############
# MULTISITE #
#############

rgw_multisite: false
rgw_zone: default
```

2. Edit the Zone Config `group_vars/boston.yml` for the Primary cluster
```
cp group_vars/zone.yml.sample group_vars/boston.yml
```

```
rgw_zone: boston

rgw_zonemaster: true
rgw_zonesecondary: false

rgw_zonegroup: massachusetts

rgw_zonegroupmaster: true
```

3. Edit the Realm Config `group_vars/usa.yml` for the Primary cluster
```
cp group_vars/realm.yml.sample group_vars/usa.yml
```

```
rgw_realm: usa

system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt

rgw_zone_user: bostonian
rgw_zone_user_display_name: "Mark Wahlberg"

rgw_pull_port: "{{ radosgw_frontend_port }}"
rgw_pull_proto: "http"
rgw_pullhost: 192.168.216.145 # IP address for rgws-000
```

5. Run the ceph-ansible playbook for the 1st cluster

3. **(Optional)** Edit the rgws.yml in group_vars for rgw related pool creation

```
rgw_create_pools:
  "{{ rgw_zone }}.rgw.buckets.data":
    pg_num: 64
    size: ""
    type: ec
    ec_profile: myecprofile
    ec_k: 5
    ec_m: 3
  "{{ rgw_zone }}.rgw.buckets.index":
    pg_num: 8
    size: ""
    type: replicated
```

**Note:** A pgcalc tool should be used to determine the optimal sizes for the rgw.buckets.data, rgw.buckets.index pools as well as any other pools declared in this dictionary.

4. Run the ceph-ansible playbook on your 1st cluster

## Configuring the Secondary Zone in a Separate Cluster

This deployment will setup a secondary zone with a different Ceph cluster as it's backend.
The secondary zone will have the same realm, and zonegroup that was created in the primary Ceph cluster.

The following inventory file will be used for the secondary cluster:
```
[rgws]

[rgws:children]
usa

[usa]
[usa:children]
salem

[salem]
	rgws-000 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.215.178
```

1. Edit `group_vars/all.yml` for the Secondary Cluster

```
## Rados Gateway options
#
radosgw_num_instances: 1

#############
# MULTISITE #
#############

rgw_multisite: false
rgw_zone: default
```

**Note:** `radosgw_num_instances` must be set to 1. The playbooks do not support deploying RGW Multisite on hosts with more than 1 RGW.

2. Edit the Zone Config `group_vars/salem.yml` for the Secondary Cluster
```
cp group_vars/zone.yml.sample group_vars/boston.yml
```

```
rgw_zone: salem

rgw_zonemaster: false
rgw_zonesecondary: true

rgw_zonegroup: massachussets

rgw_zonegroupmaster: true
```

**Note:** `rgw_zonesecondary` is set to `true` here and `rgw_zonemaster` is set to `false`.

3. Use the Exact Same Realm Config `group_vars/usa.yml` from the Primary cluster

```
rgw_realm: usa

system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt

rgw_zone_user: bostonian
rgw_zone_user_display_name: "Mark Wahlberg"

rgw_pull_port: "{{ radosgw_frontend_port }}"
rgw_pull_proto: "http"
rgw_pullhost: 192.168.216.145 # IP address for rgws-000 from the primary cluster.
```

**Note:** The endpoint made from `rgw_pull_proto` + `rgw_pull_host` + `rgw_pull_port` must be resolvable by the secondary Ceph clusters mon and rgw node(s).

5. Run the ceph-ansible playbook on your 2nd cluster

6. **(Optional)** Edit the rgws.yml in group_vars for rgw related pool creation

```
rgw_create_pools:
  "{{ rgw_zone }}.rgw.buckets.data":
    pg_num: 64
    size: ""
    type: ec
    ec_profile: myecprofile
    ec_k: 5
    ec_m: 3
  "{{ rgw_zone }}.rgw.buckets.index":
    pg_num: 8
    size: ""
    type: replicated
```
**Note:** The pg_num values should match the values for the rgw pools created on the primary cluster. Mismatching pg_num values on different sites can result in very poor performance.

**Note:** An online pgcalc tool (ex: https://ceph.io/pgcalc) should be used to determine the optimal sizes for the rgw.buckets.data, rgw.buckets.index pools as well as any other pools declared in this dictionary.

7. Run the ceph-ansible playbook on your 2nd cluster

## Conclusion

You should now have a master zone on the primary cluster and a secondary zone on secondary cluster in Active-Active mode.

# Deployment Scenario #2: Single Ceph Cluster with Multiple Realms

This deployment will setup two realms. One realm will have two different zones and zonegroups. The other will just have one zone and zonegroup.

The following inventory file will be used for the cluster:
```
[rgws]

[rgws:children]
usa
canada

[usa]
[usa:children]
boston
seattle

[boston]
	rgws-000 ansible_ssh_host=192.168.216.145 ansible_ssh_port=22 radosgw_address=192.168.216.145
[seattle]
	rgws-001 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.215.178

[canada]
[canada:children]
toronto

[toronto]
	rgws-002 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.215.199
	rgws-003 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.194.109
```

1. Generate System Access and System Secret Keys for the Realms "usa" and "canada"

```
echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > usa-multi-site-keys.txt
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> usa-multi-site-keys.txt

echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > canada-multi-site-keys.txt
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> canada-multi-site-keys.txt
```
2. Edit `group_vars/all.yml` for the Cluster

```
## Rados Gateway options
#
radosgw_num_instances: 1

#############
# MULTISITE #
#############

rgw_multisite: false
rgw_zone: default
```

2. Edit the Zone Configs `group_vars/{boston, seattle, toronto}.yml`
```
for i in {boston,seattle,toronto}; do cp group_vars/zone.yml.sample group_vars/$i.yml; done
```

```
rgw_zone: boston

rgw_zonemaster: true
rgw_zonesecondary: false

rgw_zonegroup: massachusetts

rgw_zonegroupmaster: true
```

```
rgw_zone: seattle

rgw_zonemaster: true
rgw_zonesecondary: false

rgw_zonegroup: washington

rgw_zonegroupmaster: false
```

```
rgw_zone: toronto

rgw_zonemaster: true
rgw_zonesecondary: false

rgw_zonegroup: ontario

rgw_zonegroupmaster: true
```

**Note** Since boston and seattle are in different zonegroups (massachussetts and washington) they can both be master zones.

3. Edit the Realm Configs `group_vars/{usa, canada}.yml`
```
for i in {usa,canada}; do cp group_vars/realm.yml.sample group_vars/$i.yml; done
```

```
rgw_realm: usa

system_access_key: usaaccesskey
system_secret_key: usasecretkey

rgw_realm_system_user: bostonian
rgw_realm_system_user_display_name: "Mark Wahlberg"

rgw_pull_port: "{{ radosgw_frontend_port }}"
rgw_pull_proto: "http"
rgw_pullhost: 192.168.216.145 # ipn address for rgws-000
```

```
rgw_realm: canada

system_access_key: canadaaccesskey
system_secret_key: canadasecretkey

rgw_realm_system_user: canadian
rgw_realm_system_user_display_name: "Justin Trudeau"

rgw_pull_port: "{{ radosgw_frontend_port }}"
rgw_pull_proto: "http"
rgw_pullhost: 192.168.215.199 # IP address for rgws-002
```

**Note** The secret keys and access keys should be replaced the ones generated in step #1

**Note:** The endpoint made from `rgw_pull_proto` + `rgw_pull_host` + `rgw_pull_port` for each realm should be resolvable by the mons and rgws since they are in the same Ceph cluster.

5. Run the ceph-ansible playbook

