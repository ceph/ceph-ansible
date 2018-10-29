RGW Multisite
=============

Directions for configuring the RGW Multisite support in ceph-ansible

## Requirements

* At least 2 Ceph clusters
* 1 RGW per cluster
* Jewel or newer

More details:

* Can configure a Master and Secondary realm/zonegroup/zone on 2 separate clusters.

## Configuring the Master Zone in the Primary Cluster

This will setup the realm, zonegroup and master zone and make them the defaults.  It will also reconfigure the specified RGW for use with the zone.

``
1. Generate System Access and System Secret Keys

```
echo system_access_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1) > multi-site-keys.txt
echo system_secret_key: $(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1) >> multi-site-keys.txt
```
2. Edit the RGW Group Vars

```
copy_admin_key: true
# Enable Multisite support
rgw_multisite: true
rgw_zone: jupiter
rgw_zonemaster: true
rgw_zonesecondary: false
rgw_multisite_endpoint_addr: "{{ ansible_fqdn }}"
rgw_zonegroup: solarsystem
rgw_zone_user: zone.user
rgw_realm: milkyway
system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt
```

**Note:** replace the system_access_key and system_secret_key values with the ones you generated
**Note:** rgw_zonemaster should have the value of true and rgw_zonesecondary should be false

3. Run the ceph-ansible playbook on your 1st cluster

## Configuring the Secondary Zone in a Separate Cluster

4. Edit the RGW Group Vars

```
copy_admin_key: true
# Enable Multisite support
rgw_multisite: true
rgw_zone: mars
rgw_zonemaster: false
rgw_zonesecondary: true
rgw_multisite_endpoint_addr: "{{ ansible_fqdn }}"
rgw_zonegroup: solarsystem
rgw_zone_user: zone.user
rgw_realm: milkyway
system_access_key: 6kWkikvapSnHyE22P7nO
system_secret_key: MGecsMrWtKZgngOHZdrd6d3JxGO5CPWgT2lcnpSt
rgw_pull_proto: http
rgw_pull_port: 8080
rgw_pullhost: cluster0-rgw0
```

**Note:** pullhost should be the rgw_multisite_endpoint_addr of the RGW that is configured as the Zone Master
**Note:** rgw_zone_user, system_access_key, and system_secret_key should match what you used in the master cluster
**Note:** rgw_zonemaster should have the value of false and rgw_zonesecondary should be true


5. Run the ceph-ansible playbook on your 2nd cluster

## Conclusion

You should now have a master zone on cluster0 and a secondary zone on cluster1 in an Active-Active mode.
