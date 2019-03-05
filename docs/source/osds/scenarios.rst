OSD Scenarios
=============

There are a few *scenarios* that are supported and the differences are mainly
based on the Ceph tooling required to provision OSDs, but can also affect how
devices are being configured to create an OSD.

Supported values for the required ``osd_scenario`` variable are:

* :ref:`collocated <osd_scenario_collocated>`
* :ref:`non-collocated <osd_scenario_non_collocated>`
* :ref:`lvm <osd_scenario_lvm>`

Since the Ceph mimic release, it is preferred to use the :ref:`lvm scenario
<osd_scenario_lvm>` that uses the ``ceph-volume`` provisioning tool. Any other
scenario will cause deprecation warnings.

All the scenarios mentionned above support both containerized and non-containerized cluster.
As a reminder, deploying a containerized cluster can be done by setting ``containerized_deployment``
to ``True``.

.. _osd_scenario_lvm:

lvm
---

This OSD scenario uses ``ceph-volume`` to create OSDs, primarily using LVM, and
is only available when the Ceph release is luminous or newer.

**It is the preferred method of provisioning OSDs.**

It is enabled with the following setting::


    osd_scenario: lvm

Other (optional) supported settings:

- ``osd_objectstore``: Set the Ceph *objectstore* for the OSD. Available options
  are ``filestore`` or ``bluestore``.  You can only select ``bluestore`` with
  the Ceph release is luminous or greater. Defaults to ``bluestore`` if unset.

- ``dmcrypt``: Enable Ceph's encryption on OSDs using ``dmcrypt``.
    Defaults to ``false`` if unset.

- ``osds_per_device``: Provision more than 1 OSD (the default if unset) per device.


Simple configuration
^^^^^^^^^^^^^^^^^^^^

With this approach, most of the decisions on how devices are configured to
provision an OSD are made by the Ceph tooling (``ceph-volume lvm batch`` in
this case).  There is almost no room to modify how the OSD is composed given an
input of devices.

To use this configuration, the ``devices`` option must be populated with the
raw device paths that will be used to provision the OSDs.


.. note:: Raw devices must be "clean", without a gpt partition table, or
          logical volumes present.


For example, for a node that has ``/dev/sda`` and ``/dev/sdb`` intended for
Ceph usage, the configuration would be:


.. code-block:: yaml

   osd_scenario: lvm
   devices:
     - /dev/sda
     - /dev/sdb

In the above case, if both devices are spinning drives, 2 OSDs would be
created, each with its own collocated journal.

Other provisioning strategies are possible, by mixing spinning and solid state
devices, for example:

.. code-block:: yaml

   osd_scenario: lvm
   devices:
     - /dev/sda
     - /dev/sdb
     - /dev/nvme0n1

Similar to the initial example, this would end up producing 2 OSDs, but data
would be placed on the slower spinning drives (``/dev/sda``, and ``/dev/sdb``)
and journals would be placed on the faster solid state device ``/dev/nvme0n1``.
The ``ceph-volume`` tool describes this in detail in
`the "batch" subcommand section <http://docs.ceph.com/docs/master/ceph-volume/lvm/batch/>`_

This option can also be used with ``osd_auto_discovery``, meaning that you do not need to populate
``devices`` directly and any appropriate devices found by ansible will be used instead.

.. code-block:: yaml

   osd_scenario: lvm
   osd_auto_discovery: true

Other (optional) supported settings:

- ``crush_device_class``: Sets the CRUSH device class for all OSDs created with this
  method (it is not possible to have a per-OSD CRUSH device class using the *simple*
  configuration approach). Values *must be* a string, like
  ``crush_device_class: "ssd"``


Advanced configuration
^^^^^^^^^^^^^^^^^^^^^^

This configuration is useful when more granular control is wanted when setting
up devices and how they should be arranged to provision an OSD. It requires an
existing setup of volume groups and logical volumes (``ceph-volume`` will **not**
create these).

To use this configuration, the ``lvm_volumes`` option must be populated with
logical volumes and volume groups. Additionally, absolute paths to partitions
*can* be used for ``journal``, ``block.db``, and ``block.wal``.

.. note:: This configuration uses ``ceph-volume lvm create`` to provision OSDs

Supported ``lvm_volumes`` configuration settings:

- ``data``: The logical volume name or full path to a raw device (an LV will be
  created using 100% of the raw device)

- ``data_vg``: The volume group name, **required** if ``data`` is a logical volume.

- ``crush_device_class``: CRUSH device class name for the resulting OSD, allows
  setting set the device class for each OSD, unlike the global ``crush_device_class``
  that sets them for all OSDs.

.. note:: If you wish to set the ``crush_device_class`` for the OSDs
          when using ``devices`` you must set it using the global ``crush_device_class``
          option as shown above. There is no way to define a specific CRUSH device class
          per OSD when using ``devices`` like there is for ``lvm_volumes``.


``filestore`` objectstore variables:

- ``journal``: The logical volume name or full path to a partition.

- ``journal_vg``: The volume group name, **required** if ``journal`` is a logical volume.

.. warning:: Each entry must be unique, duplicate values are not allowed


``bluestore`` objectstore variables:

- ``db``: The logical volume name or full path to a partition.

- ``db_vg``: The volume group name, **required** if ``db`` is a logical volume.

- ``wal``: The logical volume name or full path to a partition.

- ``wal_vg``: The volume group name, **required** if ``wal`` is a logical volume.


.. note:: These ``bluestore`` variables are optional optimizations. Bluestore's
          ``db`` and ``wal`` will only benefit from faster devices. It is possible to
          create a bluestore OSD with a single raw device.

.. warning:: Each entry must be unique, duplicate values are not allowed


``bluestore`` example using raw devices:

.. code-block:: yaml

   osd_objectstore: bluestore
   osd_scenario: lvm
   lvm_volumes:
     - data: /dev/sda
     - data: /dev/sdb

.. note:: Volume groups and logical volumes will be created in this case,
          utilizing 100% of the devices.

``bluestore`` example with logical volumes:

.. code-block:: yaml

   osd_objectstore: bluestore
   osd_scenario: lvm
   lvm_volumes:
     - data: data-lv1
       data_vg: data-vg1
     - data: data-lv2
       data_vg: data-vg2

.. note:: Volume groups and logical volumes must exist.


``bluestore`` example defining ``wal`` and ``db`` logical volumes:

.. code-block:: yaml

   osd_objectstore: bluestore
   osd_scenario: lvm
   lvm_volumes:
     - data: data-lv1
       data_vg: data-vg1
       db: db-lv1
       db_vg: db-vg1
       wal: wal-lv1
       wal_vg: wal-vg1
     - data: data-lv2
       data_vg: data-vg2
       db: db-lv2
       db_vg: db-vg2
       wal: wal-lv2
       wal_vg: wal-vg2

.. note:: Volume groups and logical volumes must exist.


``filestore`` example with logical volumes:

.. code-block:: yaml

   osd_objectstore: filestore
   osd_scenario: lvm
   lvm_volumes:
     - data: data-lv1
       data_vg: data-vg1
       journal: journal-lv1
       journal_vg: journal-vg1
     - data: data-lv2
       data_vg: data-vg2
       journal: journal-lv2
       journal_vg: journal-vg2

.. note:: Volume groups and logical volumes must exist.


.. _osd_scenario_collocated:

collocated
----------

.. warning:: This scenario is deprecated in the Ceph mimic release, and fully
             removed in newer releases. It is recommended to used the
             :ref:`lvm scenario <osd_scenario_lvm>` instead

This OSD scenario uses ``ceph-disk`` to create OSDs with collocated journals
from raw devices.

Use ``osd_scenario: collocated`` to enable this scenario. This scenario also
has the following required configuration options:

- ``devices``

This scenario has the following optional configuration options:

- ``osd_objectstore``: defaults to ``filestore`` if not set. Available options are ``filestore`` or ``bluestore``.
  You can only select ``bluestore`` if the Ceph release is luminous or greater.

- ``dmcrypt``: defaults to ``false`` if not set.

This scenario supports encrypting your OSDs by setting ``dmcrypt: True``.

If ``osd_objectstore: filestore`` is enabled both 'ceph data' and 'ceph journal' partitions
will be stored on the same device.

If ``osd_objectstore: bluestore`` is enabled 'ceph data', 'ceph block', 'ceph block.db', 'ceph block.wal' will be stored
on the same device. The device will get 2 partitions:

- One for 'data', called 'ceph data'

- One for 'ceph block', 'ceph block.db', 'ceph block.wal' called 'ceph block'

Example of what you will get:

.. code-block:: console

   [root@ceph-osd0 ~]# blkid /dev/sda*
   /dev/sda: PTTYPE="gpt"
   /dev/sda1: UUID="9c43e346-dd6e-431f-92d8-cbed4ccb25f6" TYPE="xfs" PARTLABEL="ceph data" PARTUUID="749c71c9-ed8f-4930-82a7-a48a3bcdb1c7"
   /dev/sda2: PARTLABEL="ceph block" PARTUUID="e6ca3e1d-4702-4569-abfa-e285de328e9d"

An example of using the ``collocated`` OSD scenario with encryption would look like:

.. code-block:: yaml

   osd_scenario: collocated
   dmcrypt: true
   devices:
     - /dev/sda
     - /dev/sdb


.. _osd_scenario_non_collocated:

non-collocated
--------------

.. warning:: This scenario is deprecated in the Ceph mimic release, and fully
             removed in newer releases. It is recommended to used the
             :ref:`lvm scenario <osd_scenario_lvm>` instead

This OSD scenario uses ``ceph-disk`` to create OSDs from raw devices with journals that
exist on a dedicated device.

Use ``osd_scenario: non-collocated`` to enable this scenario. This scenario also
has the following required configuration options:

- ``devices``

This scenario has the following optional configuration options:

- ``dedicated_devices``: defaults to ``devices`` if not set

- ``osd_objectstore``: defaults to ``filestore`` if not set. Available options are ``filestore`` or ``bluestore``.
  You can only select ``bluestore`` with the Ceph release is luminous or greater.

- ``dmcrypt``: defaults to ``false`` if not set.

This scenario supports encrypting your OSDs by setting ``dmcrypt: True``.

If ``osd_objectstore: filestore`` is enabled 'ceph data' and 'ceph journal' partitions
will be stored on different devices:
- 'ceph data' will be stored on the device listed in ``devices``
- 'ceph journal' will be stored on the device listed in ``dedicated_devices``

Let's take an example, imagine ``devices`` was declared like this:

.. code-block:: yaml

   devices:
     - /dev/sda
     - /dev/sdb
     - /dev/sdc
     - /dev/sdd

And ``dedicated_devices`` was declared like this:

.. code-block:: yaml

   dedicated_devices:
     - /dev/sdf
     - /dev/sdf
     - /dev/sdg
     - /dev/sdg

This will result in the following mapping:

- ``/dev/sda`` will have ``/dev/sdf1`` as journal

- ``/dev/sdb`` will have ``/dev/sdf2`` as a journal

- ``/dev/sdc`` will have ``/dev/sdg1`` as a journal

- ``/dev/sdd`` will have ``/dev/sdg2`` as a journal


If ``osd_objectstore: bluestore`` is enabled, both 'ceph block.db' and 'ceph block.wal' partitions will be stored
on a dedicated device.

So the following will happen:

- The devices listed in ``devices`` will get 2 partitions, one for 'block' and one for 'data'. 'data' is only 100MB
  big and do not store any of your data, it's just a bunch of Ceph metadata. 'block' will store all your actual data.

- The devices in ``dedicated_devices`` will get 1 partition for RocksDB DB, called 'block.db' and one for RocksDB WAL, called 'block.wal'

By default ``dedicated_devices`` will represent block.db

Example of what you will get:

.. code-block:: console

   [root@ceph-osd0 ~]# blkid /dev/sd*
   /dev/sda: PTTYPE="gpt"
   /dev/sda1: UUID="c6821801-2f21-4980-add0-b7fc8bd424d5" TYPE="xfs" PARTLABEL="ceph data" PARTUUID="f2cc6fa8-5b41-4428-8d3f-6187453464d0"
   /dev/sda2: PARTLABEL="ceph block" PARTUUID="ea454807-983a-4cf2-899e-b2680643bc1c"
   /dev/sdb: PTTYPE="gpt"
   /dev/sdb1: PARTLABEL="ceph block.db" PARTUUID="af5b2d74-4c08-42cf-be57-7248c739e217"
   /dev/sdb2: PARTLABEL="ceph block.wal" PARTUUID="af3f8327-9aa9-4c2b-a497-cf0fe96d126a"

There is more device granularity for Bluestore ONLY if ``osd_objectstore: bluestore`` is enabled by setting the
``bluestore_wal_devices`` config option.

By default, if ``bluestore_wal_devices`` is empty, it will get the content of ``dedicated_devices``.
If set, then you will have a dedicated partition on a specific device for block.wal.

Example of what you will get:

.. code-block:: console

   [root@ceph-osd0 ~]# blkid /dev/sd*
   /dev/sda: PTTYPE="gpt"
   /dev/sda1: UUID="39241ae9-d119-4335-96b3-0898da8f45ce" TYPE="xfs" PARTLABEL="ceph data" PARTUUID="961e7313-bdb7-49e7-9ae7-077d65c4c669"
   /dev/sda2: PARTLABEL="ceph block" PARTUUID="bff8e54e-b780-4ece-aa16-3b2f2b8eb699"
   /dev/sdb: PTTYPE="gpt"
   /dev/sdb1: PARTLABEL="ceph block.db" PARTUUID="0734f6b6-cc94-49e9-93de-ba7e1d5b79e3"
   /dev/sdc: PTTYPE="gpt"
   /dev/sdc1: PARTLABEL="ceph block.wal" PARTUUID="824b84ba-6777-4272-bbbd-bfe2a25cecf3"

An example of using the ``non-collocated`` OSD scenario with encryption, bluestore and dedicated wal devices would look like:

.. code-block:: yaml

   osd_scenario: non-collocated
   osd_objectstore: bluestore
   dmcrypt: true
   devices:
     - /dev/sda
     - /dev/sdb
   dedicated_devices:
     - /dev/sdc
     - /dev/sdc
   bluestore_wal_devices:
     - /dev/sdd
     - /dev/sdd
