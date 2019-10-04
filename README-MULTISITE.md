RGW Multisite
=============

This document contains directions for configuring the RGW Multisite support in ceph-ansible when the desired multisite configuration involves only one realm, one zone group and one zone in a cluster.

For information on configuring RGW Multisite with multiple realms, zone groups, or zones in a cluster, refer to [README-MULTISITE-MULTIREALM.md](README-MULTISITE-MULTIREALM.md).

In Ceph Multisite, a realm, master zone group, and a master zone is created on a Primary Ceph Cluster.

The realm on the primary cluster is pulled onto a secondary cluster where a new zone is created and joins the realm.

Once the realm is pulled on the secondary cluster and the new zone is created, data will now sync between the primary and secondary clusters.

## Requirements

Multisite replication can be configured either over multiple Ceph clusters or in a single Ceph cluster using Ceph version **Jewel or newer**.

* At least 2 Ceph clusters
* at least 1 RGW per cluster
* 1 RGW per host
* Jewel or newer

## Configuring the Master Zone in the Primary Ceph Cluster

This will setup the realm, master zonegroup and master zone and make them the defaults on the Primary Cluster.

``
1. Generate System Access and System Secret Keys

```
echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > multi-site-keys.txt
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> multi-site-keys.txt
```
2. Edit `group_vars/all.yml` for the Primary Cluster

```
## Rados Gateway options
#
radosgw_num_instances: 1

#############
# MULTISITE #
#############

# Enable Multisite support
rgw_multisite: true
rgw_zone: jupiter
rgw_zonemaster: true
rgw_zonegroupmaster: true
rgw_zonesecondary: false
rgw_multisite_proto: "http"
rgw_zonegroup: solarsystem
rgw_zone_user: zone.user
rgw_zone_user_display_name: "Zone User"
rgw_realm: milkyway
system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt
```

**Note**: `radosgw_num_instances` must be set to 1. The playbooks do not support deploying RGW Multisite on hosts with more than 1 RGW.

**Note:** `rgw_zone` cannot be set to "default"

**Note:** `rgw_zonemaster` should have the value of `true` and `rgw_zonesecondary` should be `false`

**Note:** replace the `system_access_key` and `system_secret_key` values with the ones you generated

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

## Pulling the Realm and Configuring a New Zone on a Secondary Ceph Cluster

This configuration will pull the realm from the primary cluster onto the secondary cluster and create a new zone on the cluster as well.

5. Edit `group_vars/all.yml` for the Secondary Cluster

```
## Rados Gateway options
#
radosgw_num_instances: 1

#############
# MULTISITE #
#############

rgw_multisite: true
rgw_zone: mars
rgw_zonemaster: false
rgw_zonesecondary: true
rgw_zonegroupmaster: false
rgw_multisite_proto: "http"
rgw_zonegroup: solarsystem
rgw_zone_user: zone.user
rgw_zone_user_display_name: "Zone User"
rgw_realm: milkyway
system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt
rgw_pull_proto: http
rgw_pull_port: 8080
rgw_pullhost: cluster0-rgw0
```

**Note:** `rgw_zone` cannot be set to "default"

**Note:** `rgw_zonemaster` should have the value of `false` and `rgw_zonesecondary` should be `true`

**Note:** The endpoint made from `rgw_pull_proto` + `rgw_pull_host` + `rgw_pull_port` for each realm should be resolvable by the Primary Ceph clusters mons and rgws

**Note:** `rgw_zone_user`, `system_access_key`, and `system_secret_key` should match what you used in the Primary Cluster

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

You should now have a master zone on cluster0 and a secondary zone on cluster1 in an Active-Active mode.
