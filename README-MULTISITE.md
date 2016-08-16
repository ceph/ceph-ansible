RGW Multisite (Experimental)
============================

Directions for configuring the RGW Multisite support in ceph-ansible

## Requirements

* At least 2 Ceph clusters
* 1 RGW per cluster
* Jewel or newer

More details:

* Can configure a Master and Secondary realm/zonegroup/zone on 2 separate clusters.


## Configuring the Master Zone in the Primary Cluster

This will setup the realm, zonegroup and master zone and make them the defaults.  It will also reconfigure the specified RGW for use with the zone.

1. Edit the Inventory File

```
[rgws]
cluster0-rgw0 rgw_zone=us-east rgw_zonemaster=true
```
1. Generate System Access and System Secret Keys

```
echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > multi-site-keys.sh
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> multi-site-keys.sh
```
1. Edit the RGW Group Vars

```
copy_admin_key: true
# Enable Multisite support
rgw_multisite: true
rgw_realm: gold
rgw_zonegroup: us
system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt
```

**Note:** replace the system_access_key and system_secret_key values with the ones you generated

1. Run the ceph-ansible playbook on your 1st cluster

Note: If you have already installed a cluster with ceph-ansible, you can use the `rgw-configure.yml` playbook as a shortcut (Only runs the ceph-rgw role)

## Configuring the Secondary Zone in a Separate Cluster

```
[rgws]
cluster1-rgw0 rgw_zone=us-west rgw_zonesecondary=true
```

1. Edit the RGW Group Vars

```
copy_admin_key: true
# Enable Multisite support
rgw_multisite: true
rgw_realm: gold
rgw_zonegroup: us
rgw_pullhost: cluster1-rgw0.fqdn
system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt
```

**Note:** pullhost should be the host of the RGW that is configured as the Zone Master
**Note:** system_access_key and system_secret_key should match what you used in the 1st cluster


1. Run the ceph-ansible playbook on your 2nd cluster

Note: If you have already installed a cluster with ceph-ansible, you can use the `rgw-configure.yml` playbook as a shortcut (Only runs the ceph-rgw role)

## Conclusion

You should now have a master zone on cluster0 and a secondary zone on cluster1 in an Active-Active mode.
