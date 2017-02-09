Selecting disks to be used by Ceph-Ansible
==========================================

# Why do we need a module for selecting disks ?

The legacy approach to select disks on a set of servers is to use their logical names like "*/dev/sdx*".

Using a logical name to point a device have the following drawbacks:

* the device path is not consistent over time : {add|remov}ing devices change the name
* it doesn't make a guarantee the proper device is targeted
* having many disks per nodes makes the list very verbose : a node can have dozens of disks
* maintaining a list of devices across many servers is a difficult tasks : many variable disks name to remember

This get to a point where we need a way to get a descriptive way to define disk's lists.

# What are the main features of this module ?

To avoid of the corner cases listed, this module offer to :

* describe disks by their capabilities/features rather than by their logical disk path
* defining the number of disks we want per description
* taking care of disks already configured
* removing disks that doesn't match some criterias
* using a consistent path which is not impacted by disk's addition/removal
* sorting devices to get a consistent list of disks over time

# How does this works ?

The **setup** module provides the *ansible_devices* data structures which reports all the available disks on a system.

We apply on top of it some filters made of the same syntax as the *ansible_devices* structure and select the appropriate disks.

If the system match the expectations, the matching device list is returned via the *devices* structure.

# How can I use it ?

## Step 1: listing the hardware

Get the output of the ansible command on a node that have the disk type you are interested in :



    [root@host] ansible localhost -m setup -a filter="ansible_devices"
                localhost | SUCCESS => {
                "ansible_facts": {
                    "ansible_devices": {
                        "sda": {
                            "holders": [], 
                            "host": "RAID bus controller: LSI Logic / Symbios Logic MegaRAID SAS 2208 [Thunderbolt] (rev 01)", 
                            "model": "PERC H710P", 
                            "partitions": {
                                "sda1": {
                                    "holders": [], 
                                    "sectors": "1024000", 
                                    "sectorsize": 512, 
                                    "size": "500.00 MB", 
                                    "start": "2048", 
                                    "uuid": "941138c1-7614-498a-911a-d20bd8a02223"
                                }, 
                                "sda2": {
                                    "holders": [
                                        "rhel_gprfs033-root", 
                                        "rhel_gprfs033-swap", 
                                        "rhel_gprfs033-home"
                                    ], 
                                    "sectors": "974673920", 
                                    "sectorsize": 512, 
                                    "size": "464.76 GB", 
                                    "start": "1026048", 
                                    "uuid": null
                                }
                            }, 
                            "removable": "0", 
                            "rotational": "1", 
                            "sas_address": null, 
                            "sas_device_handle": null, 
                            "scheduler_mode": "deadline", 
                            "sectors": "975699968", 
                            "sectorsize": "512", 
                            "size": "465.25 GB", 
                            "support_discard": "0", 
                            "vendor": "DELL"
                        }, 
                     "sdb": {
            ....
    [root@host]

Any of the reported items can be used to create a profile of the disk we look for.

To describe this device, we only keep generic features that match several disks but also get some *informative* input like :

* vendor
* model
* size
* rotational (is it a rotational disk or a SSD/flash one ?)

## Step 2: creating the profile

From the above hardware description, we can extract relevant information and put them into the following syntax :

        {"profile_name" : { 'item 1': 'value, 'item 2' : value, count : 1, 'ceph_type' : 'data' }}

* **profile name**: a semantic name to indicate what kind of disks we are targeting.

* **'item' : 'value'** : *item* is the feature you look at like 'vendor' and *value* is the associated value like *DELL* here.

* **count** : mandatory option to define the number of devices you want, starting from 1. If you want to match all the disks without taking care of the number, then use the **'*'** amount.

* **ceph_type**: mandatory option that defines the kind of disk type. Could be "data" or "journal".

A typical profile for this example could be : 

       vars:
          devices: {'storage_disks': {'vendor': 'DELL', 'rotational': '1', 'model': 'PERC H710P', 'count': 1, 'ceph_type' : 'data' }}

If for any reasons, users needs to use the legacy naming by using direct path name, it can be done like :

       vars:
          devices:
            - /dev/sda
            - /dev/sdb
            - /dev/sdc
          raw_journal_devices: [ '/dev/sdf' ]

**Note:** Using this legacy naming kills most of the benefits of this module. That's mostly a workaround in case of issues. It will only filter out disks that have partitions.

## Step 3: calling the module
---
Just define a yaml file with this setup :


        - hosts: localhost
          gather_facts: false
          vars:
              devices:
                storage_disks:
                   vendor: 'DELL'
                   rotational: '1'
                   model: 'PERC H710P'
                   count: 1
                   ceph_type: 'data'
              # devices:[ '/dev/sda', '/dev/sdb', '/dev/sdc']
              raw_journal_devices: [ '/dev/sdf' ]

          tasks:
            - name: gathering facts
              setup:
            - name: choose disk
              choose_disk:
                vars: "{{vars}}"
            - debug: var=storage_devices
            - debug: var=journal_devices
            - debug: var=legacy_devices
            - debug: var=legacy_raw_journal_devices
            - debug: var=devices_to_activate


The resulting *devices* structure looks like :

            ok: [localhost] => {
                "storage_devices": [
                    "/dev/disk/by-id/scsi-36848f690e68a50001e428e4f1e211ba2"
                ]
            }

This structure reports the selected disks by using the *profile name* key padded with an increasing number : *storage_disks_000* in that example.

The properties of each matched disks are reported, while two new properties are added :

* bdev : the consistent *b*lock *dev*ice path : this path never change over time or reboots
* ceph : if this key is set, it means this disk is already having ceph partitions on it

## Step 4: using the disks

Any module that consume this 'devices' structure is now able to pick the right disk to perform a ceph configuration.

# Details & further discussions

## Matching several disks types at a time
A typical use case, is to use rotational disks for OSDs and SSDs/flash for journals. To do that the following can do it :

          devices: {'storage_disks': {'vendor': 'DELL', 'rotational': '1', 'model': 'PERC H710P', 'count': 10, 'ceph_type': 'data' }, 'journal_disks' : {'vendor': 'Samsung', 'rotational: '0', 'count: 1, 'ceph_type': 'journal'}}


## Matching disks by their size

Matching disks by size trigger two issues :

* disk sizes are not always reported in the same units : MB vs GB vs PB
* user doesn't always a perfect match but a set of disks greater or lower that a particular size

The module does convert the units automatically to allow comparison between various outputs. In addition, two functions helps are comparing the sizes :

* gt(x) : greater than (x)
* lt(x) : lower than (x)
* gte(x) : greater than or equal (x)
* lte(x) : lower than or equal(x)

A typical usage looks like : 

          devices:
            storage_disks:
               size: 'gt(800 MB)'
               rotational: 1
               count: 3
               ceph_type: 'data'

## Using native or legacy syntax

If you use the native syntax, then the *devices* variable should be used as in :

                devices: {'storage_disks': {'vendor': 'DELL', 'rotational': '1', 'model': 'PERC H710P', 'count': 10, 'ceph_type': 'data' }}

If you use the legacy syntax (aka "/dev/sdx"), then the *devices* variable should be used as in:

                devices: [ "/dev/sda", "/dev/sdb" ]

Note that one or the other should be defined, having the two simultaneously will trigger an error.

## How complex should be my profile ?

The main idea behind this module is being able to select precisely the disks used with Ceph.

### Being to simple
Having a too simple profile leads to a less accurate results and could lead to a wrong selection of disks like in :

          devices: {'storage_disks': {'size' : 'gt(1MB)', 'count': '*', 'ceph_type': 'data'}}

This is grabbing any storage device, even like usb keys. That's really a lack of control.

### Being too precise
Having a too precise profile leads to a lack of matching devices. Selecting a device by an uuid/serial number/sas address would avoid any other device to be matched.

## How to debug/understand how the code ran ?

You can run your ansible playbook with the '-vvv' option which is very verbose.

To get a full history and persistent logging, the module is generating a log file located in `/var/log/choose_disk.log`

A typical output looks like :

            ############
            # Starting #
            ############
            Detecting free devices
             Ignoring        sda : Device have exisiting partitions
             Adding          sdb : /dev/sdb
             Adding          sdc : /dev/sdc
             Adding          sdd : /dev/sdd
             Adding          sde : /dev/sde
             Adding          sdf : Ceph disk detected
             Adding          sdg : Ceph disk detected
             Adding          sdh : /dev/sdh
             Adding          sdi : /dev/sdi
             Adding          sdj : /dev/sdj
             Adding          sdk : /dev/sdk
             Adding          sdl : /dev/sdl
             Adding          sdm : /dev/sdm
            Native syntax
             disks : {'storage_disks': {'count': 3, 'rotational': '1', 'size': 'gt(800 MB)', 'ceph_type': 'data'}}
            Finding persistent disks name
             Renaming        sdb to             scsi-36848f690e68a50001e428e4f1e211ba2
             Renaming        sdc to             scsi-36848f690e68a50001e428e4f1e2b4baf
             Renaming        sdd to             scsi-36848f690e68a50001e428e501e358d6f
             Renaming        sde to             scsi-36848f690e68a50001e428e511e3fb33c
             Renaming        sdf to             scsi-36848f690e68a50001e428e511e4a6c20
             Renaming        sdg to             scsi-36848f690e68a50001e428e521e55c62b
             Renaming        sdh to             scsi-36848f690e68a50001e428e531e60f90f
             Renaming        sdi to             scsi-36848f690e68a50001e428e541e6c6027
             Renaming        sdj to             scsi-36848f690e68a50001e428e541e778a3c
             Renaming        sdk to             scsi-36848f690e68a50001e428e551e831be3
             Renaming        sdl to             scsi-36848f690e68a50001e428e561e8e3478
             Renaming        sdm to             scsi-36848f690e68a50001e428e571e9dccd1
            Looking for matches
             Inspecting storage_disks_000
                          scsi-36848f690e68a50001e428e511e4a6c20 matched
             Inspecting storage_disks_001
                          scsi-36848f690e68a50001e428e521e55c62b matched
             Inspecting storage_disks_002
                          scsi-36848f690e68a50001e428e4f1e211ba2 matched
            Matched devices   :   3 
             storage_disks_000 : /dev/disk/by-id/scsi-36848f690e68a50001e428e511e4a6c20 (ceph)
             storage_disks_001 : /dev/disk/by-id/scsi-36848f690e68a50001e428e521e55c62b (ceph)
             storage_disks_002 : /dev/disk/by-id/scsi-36848f690e68a50001e428e4f1e211ba2
            Unmatched devices :   9
             /dev/disk/by-id/scsi-36848f690e68a50001e428e4f1e2b4baf
             /dev/disk/by-id/scsi-36848f690e68a50001e428e501e358d6f
             /dev/disk/by-id/scsi-36848f690e68a50001e428e511e3fb33c
             /dev/disk/by-id/scsi-36848f690e68a50001e428e531e60f90f
             /dev/disk/by-id/scsi-36848f690e68a50001e428e541e6c6027
             /dev/disk/by-id/scsi-36848f690e68a50001e428e541e778a3c
             /dev/disk/by-id/scsi-36848f690e68a50001e428e551e831be3
             /dev/disk/by-id/scsi-36848f690e68a50001e428e561e8e3478
             /dev/disk/by-id/scsi-36848f690e68a50001e428e571e9dccd1
            2/3 disks already configured
            All searched devices were found
            #######
            # End #
            #######
