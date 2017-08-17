.. ceph-ansible documentation master file, created by
   sphinx-quickstart on Wed Apr  5 11:55:38 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ceph-ansible
============
Ansible playbooks for Ceph, the distributed filesystem.


Installation
============

github
------
You can install directly from the source on github by following these steps:

- Clone the repository::

      git clone https://github.com/ceph/ceph-ansible.git

- Next, you must decide which branch of ``ceph-ansible`` you wish to use. There
  are stable branches to choose from or you could use the master branch::

      git checkout $branch

Releases
========

The following branches should be used depending on your requirements. The ``stable-*``
branches have been QE tested and sometimes recieve backport fixes throughout their lifecycle.
The ``master`` branch should be considered experimental and used with caution.

- ``stable-2.1`` Support for ceph version ``jewel``. This branch supports ansible versions
  ``2.1`` and ``2.2.1``.

- ``stable-2.2`` Support for ceph versions ``jewel`` and ``kraken``. This branch supports ansible versions
  ``2.1`` and ``2.2.2``.

- ``master`` Support for ceph versions ``jewel``, ``kraken`` and ``luminous``. This branch supports ansible versions
  ``2.2.3`` and ``2.3.1``.

Configuration and Usage
=======================
This project assumes you have a basic knowledge of how ansible works and have already prepared your hosts for
configuration by ansible.

After you've cloned the ``ceph-ansible`` repository, selected your branch and installed ansible then you'll need to create
your inventory file, playbook and configuration for your ceph cluster.

Inventory
---------

The ansible inventory file defines the hosts in your cluster and what roles each host plays in your ceph cluster. The default
location for an inventory file is ``/etc/ansible/hosts`` but this file can be placed anywhere and used with the ``-i`` flag of
ansible-playbook. An example inventory file would look like::

    [mons]
    mon1
    mon2
    mon3

    [osds]
    osd1
    osd2
    osd3

.. note::

    For more information on ansible inventories please refer to the ansible documentation: http://docs.ansible.com/ansible/latest/intro_inventory.html

Playbook
--------

You must have a playbook to pass to the ``ansible-playbook`` command when deploying your cluster. There is a sample playbook at the root of the ``ceph-ansible``
project called ``site.yml.sample``. This playbook should work fine for most usages, but it does include by default every daemon group which might not be
appropriate for your cluster setup. Perform the following steps to prepare your playbook:

- Rename the sample playbook: ``mv site.yml.sample site.yml``

- Modify the playbook as necessary for the requirements of your cluster

.. note::

   It's important the playbook you use is placed at the root of the ``ceph-ansible`` project. This is how ansible will be able to find the roles that
   ``ceph-ansible`` provides.


ceph-ansible Configuration
--------------------------

The configuration for your ceph cluster will be set by the use of ansible variables that ``ceph-ansible`` provides. All of these options and their default
values are defined in the ``group_vars/`` directory at the root of the ``ceph-ansible`` project. Ansible will use configuration in a ``group_vars/`` directory
that is relative to your inventory file or your playbook. Inside of the ``group_vars/`` directory there are many sample ansible configuration files that relate
to each of the ceph daemon groups by their filename. For example, the ``osds.yml.sample`` contains all the default configuation for the OSD daemons. The ``all.yml.sample``
file is a special ``group_vars`` file that applies to all hosts in your cluster.

.. note::

    For more information on setting group or host specific configuration refer to the ansible documentation: http://docs.ansible.com/ansible/latest/intro_inventory.html#splitting-out-host-and-group-specific-data

At the most basic level you must tell ``ceph-ansible`` what version of ceph you wish to install, the method of installation, your clusters network settings and
how you want your OSDs configured. To begin your configuration rename each file in ``group_vars/`` you wish to use so that it does not include the ``.sample``
at the end of the filename, uncomment the options you wish to change and provide your own value.

An example configuration that deploys the upstream ``jewel`` version of ceph with OSDs that have collocated journals would look like this in ``group_vars/all.yml``::


    ceph_stable: True
    ceph_stable_release: jewel
    public_network: "192.168.3.0/24"
    cluster_network: "192.168.4.0/24"
    monitor_interface: eth1
    journal_size: 100
    osd_objectstore: "filestore"
    devices:
      - '/dev/sda'
      - '/dev/sdb'
    osd_scenario: collocated
    # use this to set your PG config for the cluster
    ceph_conf_overrides:
      global:
        osd_pool_default_pg_num: 8
        osd_pool_default_size: 1

The following config options are required to be changed on all installations but there could be other required options depending on your OSD scenario
selection or other aspects of your cluster.

- ``ceph_stable_release``
- ``ceph_stable`` or ``ceph_rhcs`` or ``ceph_dev``
- ``public_network``
- ``osd_scenario``
- ``journal_size``
- ``monitor_interface`` or ``monitor_address``


Full documentation for configuring each of the ceph daemon types are in the following sections.


OSD Configuration
=================

OSD configuration is set by selecting an osd scenario and providing the configuration needed for
that scenario. Each scenario is different in it's requirements. Selecting your OSD scenario is done
by setting the ``osd_scenario`` configuration option.

=======
.. toctree::
   :maxdepth: 1

   osds/scenarios
    
Testing
=======

Documentation for writing functional testing scenarios for ceph-ansible.

* :doc:`Testing with ceph-ansible <testing/index>`
* :doc:`Glossary <testing/glossary>`
