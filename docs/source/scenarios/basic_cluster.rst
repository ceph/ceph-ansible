*************************
Deploying a basic cluster
*************************

Topology
========

Here we are going to describe how to deploy 3 monitors, 3 managers and 2 osds.


Writing your inventory
----------------------

.. code-block:: ini

    [mons]
    mon0
    mon1
    mon2

    [mgrs]
    mgr0
    mgr1
    mgr2

    [osds]
    osd0
    osd1

.. note::
    If you don't define a ``[mgrs]`` section, ceph-ansible will automatically collocate 1 ceph manager daemon on each monitor node.


Configuring your cluster
------------------------

Configuring your cluster can be done in many ways. There are a lot of variables that are either mandatory or optional according what you want to achieve.

By the way, these variables can be set at different places: inventory, host_vars, group_vars, etc.

We will try to identify the most common cases and cover them through this documentation.



- **ceph_origin**:
    - valid value:
        - ``repository``: Ceph will be get through a dedicated repository
        - ``distro``: Ceph will be get through the main repository already present on your distro.
        - ``local``: Ceph binaries will be copied over from the local machine
- **ceph_repository**:
    - Must be set when ``ceph_origin: repository``
    - valid value:
        - ``community``: 
        - ``rhcs``
        - ``dev``
        - ``custom``
        - ``uca``