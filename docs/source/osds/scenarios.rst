OSD Scenario
============

As of stable-4.0, the following scenarios are not supported anymore since they are associated to ``ceph-disk``:

* `collocated`
* `non-collocated`

Since the Ceph luminous release, it is preferred to use the :ref:`lvm scenario
<osd_scenario_lvm>` that uses the ``ceph-volume`` provisioning tool. Any other
scenario will cause deprecation warnings.

``ceph-disk`` was deprecated during the ceph-ansible 3.2 cycle and has been removed entirely from Ceph itself in the Nautilus version.
At present (starting from stable-4.0), there is only one scenario, which defaults to ``lvm``, see:

* :ref:`lvm <osd_scenario_lvm>`

So there is no need to configure ``osd_scenario`` anymore, it defaults to ``lvm``.

The ``lvm`` scenario mentionned above support both containerized and non-containerized cluster.
As a reminder, deploying a containerized cluster can be done by setting ``containerized_deployment``
to ``True``.

.. _osd_scenario_lvm:

lvm
---

This OSD scenario uses ``ceph-volume`` to create OSDs, primarily using LVM, and
is only available when the Ceph release is luminous or newer.
It is automatically enabled.

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

   devices:
     - /dev/sda
     - /dev/sdb

In the above case, if both devices are spinning drives, 2 OSDs would be
created, each with its own collocated journal.

Other provisioning strategies are possible, by mixing spinning and solid state
devices, for example:

.. code-block:: yaml

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
   lvm_volumes:
     - data: /dev/sda
     - data: /dev/sdb

.. note:: Volume groups and logical volumes will be created in this case,
          utilizing 100% of the devices.

``bluestore`` example with logical volumes:

.. code-block:: yaml

   osd_objectstore: bluestore
   lvm_volumes:
     - data: data-lv1
       data_vg: data-vg1
     - data: data-lv2
       data_vg: data-vg2

.. note:: Volume groups and logical volumes must exist.


``bluestore`` example defining ``wal`` and ``db`` logical volumes:

.. code-block:: yaml

   osd_objectstore: bluestore
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