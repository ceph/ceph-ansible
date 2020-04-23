RGW Multisite
=============

This document contains directions for configuring the RGW Multisite in ceph-ansible. 
Multisite replication can be configured either over multiple Ceph clusters or in a single Ceph cluster to isolate RGWs from eachother.

The first two sections are refreshers on working with ansible inventory and RGW Multisite.
The next 4 sections are instructions on deploying the following multisite scenarios:

Scenario #1: Single Realm with Multiple Ceph Clusters\ 
Scenario #2: Single Ceph Cluster with Multiple Realms\ 
Scenario #3: Multiple Realms over Multiple Ceph Clusters\
Scenario #4: Multiple Realms over Multiple Ceph Clusters with Multiple Instances on a Host\

# Working with Ansible Inventory

If you are familiar with basic ansible terminology, working with inventory files, and variable precedence feel free to skip this section.

## The Inventory File

Ceph-ansible starts up all the different daemons in a Ceph cluster. 
Each daemon (osd.0, mon.1, rgw.a) is given a line in the inventory file. Each line is called a **host** in ansible.
Each type of daemon (osd, mon, rgw, mgr, etc.) is given a **group** with its respective daemons in the ansible inventory file. 

Here is an example of an inventory file (in .ini format) for a ceph cluster with 1 ceph-mgr, 4 rgws, 3 osds, and 2 mons:
```
[mgrs]
	mgr-000 ansible_ssh_host=192.168.224.48 ansible_ssh_port=22
[rgws]
	rgws-000 ansible_ssh_host=192.168.216.145 ansible_ssh_port=22 radosgw_address=192.168.216.145
	rgws-001 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.215.178
[osds]
	osd-002 ansible_ssh_host=192.168.176.118 ansible_ssh_port=22
	osd-001 ansible_ssh_host=192.168.226.21 ansible_ssh_port=22
	osd-000 ansible_ssh_host=192.168.230.196 ansible_ssh_port=22
[mons]
	mon-000 ansible_ssh_host=192.168.210.155 ansible_ssh_port=22 monitor_address=192.168.210.155
	mon-001 ansible_ssh_host=192.168.179.111 ansible_ssh_port=22 monitor_address=192.168.179.111
```

Notice there are 4 groups defined here: mgrs, rgws, osds, mons. 
There is one host (mgr-000) in mgrs, 2 hosts (rgws-000, rgws-001) in rgws, 3 hosts (osd-000, osd-001, osd-002) in osds, and 2 hosts (mon-000, mon-001) in mons.

## group_vars

In the ceph-ansible tree there is a directory called `group_vars`. This directory has a collection of .yml files for variables set for each of the groups.
The rgw multisite specific variables are defined in `all.yml`. This file has variables that apply to all groups in the inventory.
When a variable, for example if `rgw_realm: usa`, is set in `group_vars/all.yml`, `usa` will be the value for `rgw_realm` for all of the rgws.

## host_vars

If you want to set any of the variables defined in `group_vars` for a specific host you have two options.
One option is to edit the line in the inventory file for the host you want to configure. In the above inventory each mon and rgw has a host specific variable for its address.

The preferred option is to create a directory called `host_vars` at the root of the ceph-ansible tree.
In `host_vars/` there can be files with the same name as the host (ex: osd-000, mgr-000, rgw-001) that set variables for each host.
The values for the variables set in `host_vars` have a higher precedence than the values in `group_var`.

Consider this the file `host_vars/rgw-000`:

```
rgw_realm: usa
rgw_zonegroup: alaska
rgw_zone: juneau

rgw_zonemaster: true
rgw_zonesecondary: false
system_access_key: alaskaaccesskey
system_secret_key: alaskasecretkey
```

Even if `rgw_realm` is set to `france` in `group_vars/all.yml`, `rgw_realm` will evaluate to `usa` for tasks run on `rgw-000`.
This is because Ansible gives higher precedence to the values set in `host_vars` over `group_vars`.

For more information on working with inventory in Ansible please visit: https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html.

# Brief Multisite Overview

## RGW Multisite terminology

If you are familiar with RGW multisite in detail, feel free to skip this section.

Rados gateways (RGWs) in multisite replication are grouped into zones. 

A group of 1 or more RGWs can be grouped into a **zone**.\
A group of 1 or more zones can be grouped into a **zonegroup**.\
A group of 1 or more zonegroups can be grouped into a **realm**.\
A Ceph **cluster** in multisite has 1 or more rgws that use the same backend OSDs.\ 

There can be mutliple clusters in one realm, multiple realms in a single cluster, or multiple realms over multiple clusters.

## RGW Realms

A realm allows the RGWs inside of it to be independent and isolated from RGWs outside of the realm. A realm contains one or more zonegroups.

Realms can contain 1 or more clusters. There can also be more than 1 realm in a cluster.

For more defail information on multisite please visit: https://docs.ceph.com/docs/master/radosgw/multisite/

## RGW Zonegroups

Similar to zones a zonegroup can be either **master zonegroup** or a **secondary zonegroup**.

`rgw_zonegroupmaster` specifies whether the zonegroup will be the master zonegroup in a realm.
There can only be one master zonegroup per realm. There can be any number of secondary zonegroups in a realm. 
Zonegroups that are not master must have `rgw_zonegroupmaster` set to false.

## RGW Zones

A zone is a collection of RGW daemons. A zone can be either **master zone** or a **secondary zone**.

`rgw_zonemaster` specifies that the zone will be the master zone in a zonegroup.
`rgw_zonesecondary` specifies that the zone will be a secondary zone in a zonegroup.
Both `rgw_zonemaster` and `rgw_zonesecondary` need to be defined. They cannot have the same value.

Finally, The variable `rgw_zone` is set to "default" to enable compression for clusters configured without rgw multi-site.
If multisite is configured `rgw_zone` should not be set to "default".

# Deployment Scenario #1: Single Realm & Zonegroup with Multiple Ceph Clusters

## Requirements

* At least 2 Ceph clusters
* 1 RGW per cluster
* Jewel or newer

## Configuring the Master Zone in the Primary Cluster

This will setup a realm, master zonegroup and master zone in the Ceph cluster.
Since there is only 1 realm, 1 zonegroup, and 1 zone for all the rgw hosts, only `group_vars/all.yml` needs to be edited for mulitsite conifguration.
If there is one more that one rgw being deployed in this configuration, the rgw(s) will be added to the master zone.

1. Generate System Access and System Secret Keys

```
echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > multi-site-keys.txt
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> multi-site-keys.txt
```
2. Edit `group_vars/all.yml` for the 1st cluster

```
rgw_multisite: true

rgw_zone: juneau
rgw_zonegroup: alaska
rgw_realm: usa

rgw_zonemaster: true
rgw_zonesecondary: false

rgw_zonegroupmaster: true

rgw_multisite_proto: "http"
rgw_zone_user: edward.lewis
rgw_zone_user_display_name: "Edward Lewis"

system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt
```
**Note:** `rgw_zonemaster` should have the value of `true` and `rgw_zonesecondary` should be `false`. Both values always need to be defined when running multisite.

**Note:** replace the `system_access_key` and `system_secret_key` values with the ones you generated.

3. Run the ceph-ansible playbook for the 1st cluster

## Configuring the Secondary Zone in a Separate Cluster

This will setup a realm, master zonegroup and master zone in the secondary Ceph cluster.
Since there is only 1 realm, 1 zonegroup, and 1 zone for all the rgw hosts, only `group_vars/all.yml` needs to be edited for mulitsite conifguration.
If there is one more that one rgw being deployed in this configuration, the rgw(s) will be added to the secondary zone.

4. Edit `group_vars/all.yml` for the 2nd cluster

```
rgw_multisite: true

rgw_zone: fairbanks
rgw_zonegroup: alaska
rgw_realm: usa

rgw_zonemaster: false
rgw_zonesecondary: true

rgw_zonegroupmaster: true

rgw_multisite_proto: "http"
rgw_zone_user: edward.lewis
rgw_zone_user_display_name: "Edward Lewis"

system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt

rgw_pull_proto: http
rgw_pull_port: 8080
rgw_pullhost: cluster0-rgw-000
```

**Note:** `rgw_zonemaster` should have the value of `false` and `rgw_zonesecondary` should be `true`

**Note:** The variables `rgw_pull_port`, `rgw_pull_proto`, `rgw_pullhost`, are joined together to make an endpoint string needed to create secondary zones. This endpoint is of one of the RGW endpoints in a master zone in the zonegroup and realm you want to create secondary zones in. This endpoint **must be resolvable** from the mons and rgws in the cluster the secondary zone(s)  are being created in.

**Note:** `system_access_key`, and `system_secret_key` should match what you used in the Primary Cluster

5. Run the ceph-ansible playbook on your 2nd cluster

## Conclusion

You should now have a master zone on cluster0 and a secondary zone on cluster1 in an Active-Active mode.

# Deployment Scenario #2: Single Ceph Cluster with Multiple Realms

## Requirements

* Jewel or newer

## Configuring Multiple Realms in a Single Cluster

This configuration will a single Ceph cluster with multiple realms.
Each of the rgws in the inventory should have a file in `host_vars` where the realm, zone, and zonegroup can be set for the rgw along with other variables.

1. Generate System Access and System Secret Keys for each realm

```
echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > multi-site-keys-realm-1.txt
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> multi-site-keys-realm-1.txt

echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > multi-site-keys-realm-2.txt
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> multi-site-keys-realm-2.txt
```
2. Edit `group_vars/all.yml` for the cluster

```
rgw_multisite: true
```

As previously learned, all values set here will be set on all rgw hosts. `rgw_multisite` be set to `true` for all rgw hosts so multisite playbooks can run on all rgws.

3. Create & edit files in `host_vars/` to create realms, zonegroups, and master zones.

Here is an example of the file `host_vars/rgws-000` for the `rgws-000` entry in the `[rgws]` section of for the example ansible inventory.

```
rgw_zonemaster: true
rgw_zonesecondary: false
rgw_zonegroupmaster: true
rgw_multisite_proto: "http"
rgw_realm: 'france'
rgw_zonegroup: 'idf'
rgw_zone: 'paris'
radosgw_address: "{{ _radosgw_address }}"
radosgw_frontend_port: 8080
rgw_zone_user: jacques.chirac
rgw_zone_user_display_name: "Jacques Chirac"
system_access_key: P9Eb6S8XNyo4dtZZUUMy
system_secret_key: qqHCUtfdNnpHq3PZRHW5un9l0bEBM812Uhow0XfB
```

Here is an example of the file `host_vars/rgws-001` for the `rgws-001` entry in the `[rgws]` section of for the example ansible inventory.

```
rgw_zonemaster: true
rgw_zonesecondary: false
rgw_zonegroupmaster: true
rgw_multisite_proto: "http"
rgw_realm: 'usa'
rgw_zonegroup: 'alaska'
rgw_zone: 'juneau'
radosgw_address: "{{ _radosgw_address }}"
radosgw_frontend_port: 8080
rgw_zone_user: edward.lewis
rgw_zone_user_display_name: "Edward Lewis"
system_access_key: yu17wkvAx3B8Wyn08XoF
system_secret_key: 5YZfaSUPqxSNIkZQQA3lBZ495hnIV6k2HAz710BY
```

**Note:** Since `rgw_realm`, `rgw_zonegroup`, and `rgw_zone` differ between files, a new realm, zonegroup, and master zone are created containing rgws-000 and rgws-001 respectively.

**Note:** `rgw_zonegroupmaster` is set to true in each of the files since it will be the only zonegroup in each realm.

**Note:** `rgw_zonemaster` should have the value of `true` and `rgw_zonesecondary` should be `false`.

**Note:** replace the `system_access_key` and `system_secret_key` values with the ones you generated.

5. Run the ceph-ansible playbook on your cluster

## Conclusion

The RGWs in the deployed cluster will be split up into 2 realms: `france` and `usa`. France has a zonegroup named `idf` and usa has one called `alaska`. 
`Idf` has a master zone called `paris`. `Alaska` has a  master zone called `juneau`. 

# Deployment Scenario #3: Multiple Realms over Multiple Ceph Clusters

The multisite playbooks in ceph-ansible are flexible enough to create many realms, zonegroups, and zones that span many clusters.

A multisite configuration consisting of multiple realms across multiple clusters can be configured by having files in `host_vars` for the rgws in each cluster similar to scenario #2.

The host_vars for the rgws in the second cluster would have `rgw_zonesecondary` set to true and the additional `rgw_pull` variables as seen in scenario #2

The inventory for the rgws section of the master cluster for this example looks like:

```
[rgws]
	rgws-000 ansible_ssh_host=192.168.216.145 ansible_ssh_port=22 radosgw_address=192.168.216.145
	rgws-001 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.215.178
```

The inventory for the rgws section of the secondary cluster for this example looks like:

```
[rgws]
	rgws-002 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.215.199
	rgws-003 ansible_ssh_host=192.168.215.178 ansible_ssh_port=22 radosgw_address=192.168.194.109
```

## Requirements

* At least 2 Ceph clusters
* at least 2 RGW in the master cluster and the secondary clusters
* Jewel or newer

1. Generate System Access and System Secret Keys for each realm

```
echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > multi-site-keys-realm-1.txt
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> multi-site-keys-realm-1.txt

echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > multi-site-keys-realm-2.txt
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> multi-site-keys-realm-2.txt

...
```
2. Edit `group_vars/all.yml` for the cluster

```
rgw_multisite: true
```

As per the previous example, all values set here will be set on all rgw hosts.

3. Create & edit files in `host_vars/` to create realms, zonegroups, and master zones on cluster #1.

Here is an example of the file `host_vars/rgws-000` for the the master cluster. 

```
rgw_zonemaster: true
rgw_zonesecondary: false
rgw_zonegroupmaster: true
rgw_multisite_proto: "http"
rgw_realm: 'france'
rgw_zonegroup: 'idf'
rgw_zone: 'paris'
radosgw_address: "{{ _radosgw_address }}"
radosgw_frontend_port: 8080
rgw_zone_user: jacques.chirac
rgw_zone_user_display_name: "Jacques Chirac"
system_access_key: P9Eb6S8XNyo4dtZZUUMy
system_secret_key: qqHCUtfdNnpHq3PZRHW5un9l0bEBM812Uhow0XfB
```

Here is an example of the file `host_vars/rgws-001` for the the master cluster.

```
rgw_zonemaster: true
rgw_zonesecondary: false
rgw_zonegroupmaster: true
rgw_multisite_proto: "http"
rgw_realm: 'usa'
rgw_zonegroup: 'alaska'
rgw_zone: 'juneau'
radosgw_address: "{{ _radosgw_address }}"
radosgw_frontend_port: 8080
rgw_zone_user: edward.lewis
rgw_zone_user_display_name: "Edward Lewis"
system_access_key: yu17wkvAx3B8Wyn08XoF
system_secret_key: 5YZfaSUPqxSNIkZQQA3lBZ495hnIV6k2HAz710BY
```

4. Run the ceph-ansible playbook on your master cluster.

5. Create & edit files in `host_vars/` for the entries in the `[rgws]` section of the inventory on the secondary cluster.

Here is an example of the file `host_vars/rgws-000` for the `rgws-000` entry in the `[rgws]` section of for the example ansible inventory if it was for a secondary cluster.

```
rgw_zonemaster: false
rgw_zonesecondary: true
rgw_zonegroupmaster: true
rgw_multisite_proto: "http"
rgw_realm: 'france'
rgw_zonegroup: 'idf'
rgw_zone: 'versailles'
radosgw_address: "{{ _radosgw_address }}"
radosgw_frontend_port: 8080
rgw_zone_user: jacques.chirac
rgw_zone_user_display_name: "Jacques Chirac"
system_access_key: P9Eb6S8XNyo4dtZZUUMy
system_secret_key: qqHCUtfdNnpHq3PZRHW5un9l0bEBM812Uhow0XfB
rgw_pull_proto: http
rgw_pull_port: 8080
rgw_pullhost: cluster0-rgw-000-hostname
```

Here is an example of the file `host_vars/rgws-001` for the `rgws-001` entry in the `[rgws]` section of for the example ansible inventory if it was for a secondary cluster.

```
rgw_zonemaster: false
rgw_zonesecondary: true
rgw_zonegroupmaster: true
rgw_multisite_proto: "http"
rgw_realm: 'usa'
rgw_zonegroup: 'alaska'
rgw_zone: 'juneau'
radosgw_address: "{{ _radosgw_address }}"
radosgw_frontend_port: 8080
rgw_zone_user: edward.lewis
rgw_zone_user_display_name: "Edward Lewis"
system_access_key: yu17wkvAx3B8Wyn08XoF
system_secret_key: 5YZfaSUPqxSNIkZQQA3lBZ495hnIV6k2HAz710BY
rgw_pull_proto: http
rgw_pull_port: 8080
rgw_pullhost: cluster0-rgw-001-hostname
```

6. Run the ceph-ansible playbook on your secondary cluster.

## Conclusion

There will be 2 realms in this configuration, `france` and `usa`, with RGWs and RGW zones in both clusters. Data is realm france will be replicated over both clusters and remain isolated from rgws in realm usa and vice versa.

# Deployment Scenario #4: Multiple Realms over Multiple Ceph Clusters with Multiple Instances

More than 1 RGW can be running on a single host. To configure multisite for a host with more than one rgw instance running on the host, `rgw_instances` must be configured.

Each item in `rgw_instances` (declared in a host_vars file) represents an RGW on that host. In each item is the multisite configuration for that RGW. 

Here is an example:

```
rgw_instances:
  - instance_name: 'rgw0'
    rgw_realm: 'usa'
    rgw_zonegroup: 'alaska'
    rgw_zone: 'juneau'
    radosgw_address: "{{ _radosgw_address }}"
    radosgw_frontend_port: 8080
    rgw_zone_user: edward.lewis
    rgw_zone_user_display_name: "Edward Lewis"
    system_access_key: yu17wkvAx3B8Wyn08XoF
    system_secret_key: 5YZfaSUPqxSNIkZQQA3lBZ495hnIV6k2HAz710BY
```

Here is an example of a host_vars for a host (ex: rgw-000 in the examples) containing 2 rgw_instances:

```
rgw_zonemaster: true
rgw_zonesecondary: false
rgw_zonegroupmaster: true
rgw_multisite_proto: "http"
rgw_instances:
  - instance_name: 'rgw0'
    rgw_realm: 'usa'
    rgw_zonegroup: 'alaska'
    rgw_zone: 'juneau'
    radosgw_address: "{{ _radosgw_address }}"
    radosgw_frontend_port: 8080
    rgw_zone_user: edward.lewis
    rgw_zone_user_display_name: "Edward Lewis"
    system_access_key: yu17wkvAx3B8Wyn08XoF
    system_secret_key: 5YZfaSUPqxSNIkZQQA3lBZ495hnIV6k2HAz710BY
  - instance_name: 'rgw1'
    rgw_realm: 'france'
    rgw_zonegroup: 'idf'
    rgw_zone: 'paris'
    radosgw_address: "{{ _radosgw_address }}"
    radosgw_frontend_port: 8081
    rgw_zone_user: jacques.chirac
    rgw_zone_user_display_name: "Jacques Chirac"
    system_access_key: P9Eb6S8XNyo4dtZZUUMy
    system_secret_key: qqHCUtfdNnpHq3PZRHW5un9l0bEBM812Uhow0XfB
```

This example starts up 2 rgws on host rgw-000. `rgw0` is configured to be in realm usa and `rgw1` is configured to be in realm france. 

The variables `rgw_zonemaster`, `rgw_zonesecondary`, `rgw_zonegroupmaster`, `rgw_multisite_proto` cannot be set in an item of rgw_instances. All of these variables must be set in group_vars/ or host_vars/.

`rgw_instances` can be used in host_vars for multisite deployments like scenarios 2 and 3
