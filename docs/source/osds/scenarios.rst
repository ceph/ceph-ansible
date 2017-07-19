OSD Scenarios
=============

lvm_osds
--------
This OSD scenario uses ``ceph-volume`` to create OSDs from logical volumes and
is only available when the ceph release is Luminous or greater.

.. note::
   The creation of the logical volumes is not supported by ceph-ansible, ceph-volume
   only creates OSDs from existing logical volumes.

Use ``lvm_osds:true`` to enable this scenario. Currently we only support dedicated journals
when using lvm, not collocated journals.

To configure this scenario use the ``lvm_volumes`` config option. ``lvm_volumes``  is a dictionary whose
key/value pairs represent a data lv and a journal pair. Journals can be either a lv, device or partition.
You can not use the same journal for many data lvs.

For example, a configuration to use ``lvm_osds`` would look like::
    
    lvm_osds: true

    lvm_volumes:
      data-lv1: journal-lv1
      data-lv2: /dev/sda
      data:lv3: /dev/sdb1
