OSD Scenarios
=============

lvm
---
This OSD scenario uses ``ceph-volume`` to create OSDs from logical volumes and
is only available when the ceph release is Luminous or newer.

.. note::
   The creation of the logical volumes is not supported by ``ceph-ansible``, ``ceph-volume``
   only creates OSDs from existing logical volumes.

Use ``osd_scenario: lvm`` to enable this scenario. Currently we only support dedicated journals
when using lvm, not collocated journals.

To configure this scenario use the ``lvm_volumes`` config option. ``lvm_volumes``  is a dictionary whose
key/value pairs represent a data lv and a journal pair. Journals can be either a lv, device or partition.
You can not use the same journal for many data lvs.

.. note::
   Any logical volume or logical group used in ``lvm_volumes`` must be a name and not a path.

For example, a configuration to use the ``lvm`` osd scenario would look like::
    
    osd_scenario: lvm
    lvm_volumes:
      data-lv1: journal-lv1
      data-lv2: /dev/sda
      data:lv3: /dev/sdb1
