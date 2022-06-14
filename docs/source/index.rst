============
ceph-ansible
============

Ansible playbooks for Ceph, the distributed filesystem.


Installation
============

GitHub
------

You can install directly from the source on GitHub by following these steps:

- Clone the repository:

  .. code-block:: console

     $ git clone https://github.com/ceph/ceph-ansible.git

- Next, you must decide which branch of ``ceph-ansible`` you wish to use. There
  are stable branches to choose from or you could use the main branch:

  .. code-block:: console

     $ git checkout $branch

- Next, use pip and the provided requirements.txt to install Ansible and other
  needed Python libraries:

  .. code-block:: console

     $ pip install -r requirements.txt

.. _ansible-on-rhel-family:

Ansible on RHEL and CentOS
--------------------------

You can acquire Ansible on RHEL and CentOS by installing from `Ansible channel <https://access.redhat.com/articles/3174981>`_.

On RHEL:

.. code-block:: console

   $ subscription-manager repos --enable=rhel-7-server-ansible-2-rpms

(CentOS does not use subscription-manager and already has "Extras" enabled by default.)

.. code-block:: console

   $ sudo yum install ansible

Ansible on Ubuntu
-----------------

You can acquire Ansible on Ubuntu by using the `Ansible PPA <https://launchpad.net/~ansible/+archive/ubuntu/ansible>`_.

.. code-block:: console

   $ sudo add-apt-repository ppa:ansible/ansible
   $ sudo apt update
   $ sudo apt install ansible

Ansible collections
-------------------

In order to install third-party collections that are required for ceph-ansible,
please run:

.. code-block:: console

   $ ansible-galaxy install -r requirements.yml


Releases
========

The following branches should be used depending on your requirements. The ``stable-*``
branches have been QE tested and sometimes receive backport fixes throughout their lifecycle.
The ``main`` branch should be considered experimental and used with caution.

- ``stable-3.0`` Supports Ceph versions ``jewel`` and ``luminous``. This branch requires Ansible version ``2.4``.

- ``stable-3.1`` Supports Ceph versions ``luminous`` and ``mimic``. This branch requires Ansible version ``2.4``.

- ``stable-3.2`` Supports Ceph versions ``luminous`` and ``mimic``. This branch requires Ansible version ``2.6``.

- ``stable-4.0`` Supports Ceph version ``nautilus``. This branch requires Ansible version ``2.9``.

- ``stable-5.0`` Supports Ceph version ``octopus``. This branch requires Ansible version ``2.9``.

- ``stable-6.0`` Supports Ceph version ``pacific``. This branch requires Ansible version ``2.10``.

- ``stable-7.0`` Supports Ceph version ``quincy``. This branch requires Ansible version ``2.12``.

- ``main`` Supports the main (devel) branch of Ceph. This branch requires Ansible version ``2.12``.

.. NOTE:: ``stable-3.0`` and ``stable-3.1`` branches of ceph-ansible are deprecated and no longer maintained.

Configuration and Usage
=======================

This project assumes you have a basic knowledge of how Ansible works and have already prepared your hosts for
configuration by Ansible.

After you've cloned the ``ceph-ansible`` repository, selected your branch and installed Ansible then you'll need to create
your inventory file, playbook and configuration for your Ceph cluster.

Inventory
---------

The Ansible inventory file defines the hosts in your cluster and what roles each host plays in your Ceph cluster. The default
location for an inventory file is ``/etc/ansible/hosts`` but this file can be placed anywhere and used with the ``-i`` flag of
``ansible-playbook``.

An example inventory file would look like:

.. code-block:: ini

   [mons]
   mon1
   mon2
   mon3

   [osds]
   osd1
   osd2
   osd3

.. note::

   For more information on Ansible inventories please refer to the Ansible documentation: http://docs.ansible.com/ansible/latest/intro_inventory.html

Playbook
--------

You must have a playbook to pass to the ``ansible-playbook`` command when deploying your cluster. There is a sample playbook at the root of the ``ceph-ansible``
project called ``site.yml.sample``. This playbook should work fine for most usages, but it does include by default every daemon group which might not be
appropriate for your cluster setup. Perform the following steps to prepare your playbook:

- Rename the sample playbook: ``mv site.yml.sample site.yml``

- Modify the playbook as necessary for the requirements of your cluster

.. note::

   It's important the playbook you use is placed at the root of the ``ceph-ansible`` project. This is how Ansible will be able to find the roles that
   ``ceph-ansible`` provides.

Configuration Validation
------------------------

The ``ceph-ansible`` project provides config validation through the ``ceph-validate`` role. If you are using one of the provided playbooks this role will
be run early in the deployment as to ensure you've given ``ceph-ansible`` the correct config. This check is only making sure that you've provided the
proper config settings for your cluster, not that the values in them will produce a healthy cluster. For example, if you give an incorrect address for
``monitor_address`` then the mon will still fail to join the cluster.

An example of a validation failure might look like:

.. code-block:: console

   TASK [ceph-validate : validate provided configuration] *************************
   task path: /Users/andrewschoen/dev/ceph-ansible/roles/ceph-validate/tasks/main.yml:3
   Wednesday 02 May 2018  13:48:16 -0500 (0:00:06.984)       0:00:18.803 *********
    [ERROR]: [mon0] Validation failed for variable: osd_objectstore

    [ERROR]: [mon0] Given value for osd_objectstore: foo

    [ERROR]: [mon0] Reason: osd_objectstore must be either 'bluestore' or 'filestore'

    fatal: [mon0]: FAILED! => {
        "changed": false
        }

Supported Validation
^^^^^^^^^^^^^^^^^^^^

The ``ceph-validate`` role currently supports validation of the proper config for the following
osd scenarios:

- ``collocated``
- ``non-collocated``
- ``lvm``

The following install options are also validated by the ``ceph-validate`` role:

- ``ceph_origin`` set to ``distro``
- ``ceph_origin`` set to ``repository``
- ``ceph_origin`` set to ``local``
- ``ceph_repository`` set to ``rhcs``
- ``ceph_repository`` set to ``dev``
- ``ceph_repository`` set to ``community``


Installation methods
--------------------

Ceph can be installed through several methods.

.. toctree::
   :maxdepth: 1

   installation/methods

Configuration
-------------

The configuration for your Ceph cluster will be set by the use of ansible variables that ``ceph-ansible`` provides. All of these options and their default
values are defined in the ``group_vars/`` directory at the root of the ``ceph-ansible`` project. Ansible will use configuration in a ``group_vars/`` directory
that is relative to your inventory file or your playbook. Inside of the ``group_vars/`` directory there are many sample Ansible configuration files that relate
to each of the Ceph daemon groups by their filename. For example, the ``osds.yml.sample`` contains all the default configuration for the OSD daemons. The ``all.yml.sample``
file is a special ``group_vars`` file that applies to all hosts in your cluster.

.. note::

   For more information on setting group or host specific configuration refer to the Ansible documentation: http://docs.ansible.com/ansible/latest/intro_inventory.html#splitting-out-host-and-group-specific-data

At the most basic level you must tell ``ceph-ansible`` what version of Ceph you wish to install, the method of installation, your clusters network settings and
how you want your OSDs configured. To begin your configuration rename each file in ``group_vars/`` you wish to use so that it does not include the ``.sample``
at the end of the filename, uncomment the options you wish to change and provide your own value.

An example configuration that deploys the upstream ``octopus`` version of Ceph with lvm batch method would look like this in ``group_vars/all.yml``:

.. code-block:: yaml

   ceph_origin: repository
   ceph_repository: community
   public_network: "192.168.3.0/24"
   cluster_network: "192.168.4.0/24"
   monitor_interface: eth1
   devices:
     - '/dev/sda'
     - '/dev/sdb'

The following config options are required to be changed on all installations but there could be other required options depending on your OSD scenario
selection or other aspects of your cluster.

- ``ceph_origin``
- ``public_network``
- ``monitor_interface`` or ``monitor_address``


When deploying RGW instance(s) you are required to set the ``radosgw_interface`` or ``radosgw_address`` config option.

``ceph.conf`` Configuration File
---------------------------------

The supported method for defining your ``ceph.conf`` is to use the ``ceph_conf_overrides`` variable. This allows you to specify configuration options using
an INI format. This variable can be used to override sections already defined in ``ceph.conf`` (see: ``roles/ceph-config/templates/ceph.conf.j2``) or to provide
new configuration options.

The following sections in ``ceph.conf`` are supported:

* ``[global]``
* ``[mon]``
* ``[osd]``
* ``[mds]``
* ``[client.rgw.{instance_name}]``

An example:

.. code-block:: yaml

   ceph_conf_overrides:
      global:
        foo: 1234
        bar: 5678
      osd:
        osd_mkfs_type: ext4

.. note::

   We will no longer accept pull requests that modify the ``ceph.conf`` template unless it helps the deployment. For simple configuration tweaks
   please use the ``ceph_conf_overrides`` variable.

Full documentation for configuring each of the Ceph daemon types are in the following sections.

OSD Configuration
-----------------

OSD configuration was used to be set by selecting an OSD scenario and providing the configuration needed for
that scenario. As of nautilus in stable-4.0, the only scenarios available is ``lvm``.

.. toctree::
   :maxdepth: 1

   osds/scenarios

Day-2 Operations
----------------

ceph-ansible provides a set of playbook in ``infrastructure-playbooks`` directory in order to perform some basic day-2 operations.

.. toctree::
   :maxdepth: 1

   day-2/osds
   day-2/purge
   day-2/upgrade

Contribution
============

See the following section for guidelines on how to contribute to ``ceph-ansible``.

.. toctree::
   :maxdepth: 1

   dev/index

Testing
=======

Documentation for writing functional testing scenarios for ``ceph-ansible``.

* :doc:`Testing with ceph-ansible <testing/index>`
* :doc:`Glossary <testing/glossary>`

Demos
=====

Vagrant Demo
------------

Deployment from scratch on vagrant machines: https://youtu.be/E8-96NamLDo

Bare metal demo
---------------

Deployment from scratch on bare metal machines: https://youtu.be/dv_PEp9qAqg
