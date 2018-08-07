.. _testing:

Testing
=======

``ceph-ansible`` has the ability to test different scenarios (collocated journals
or dmcrypt OSDs for example) in an isolated, repeatable, and easy way.

These tests can run locally with VirtualBox or via libvirt if available, which
removes the need to solely rely on a CI system like Jenkins to verify
a behavior.

* **Getting started:**

  * :doc:`Running a Test Scenario <running>`
  * :ref:`dependencies`

* **Configuration and structure:**

  * :ref:`layout`
  * :ref:`test_files`
  * :ref:`scenario_files`
  * :ref:`scenario_wiring`

* **Adding or modifying tests:**

  * :ref:`test_conventions`
  * :ref:`testinfra`

* **Adding or modifying a scenario:**

  * :ref:`scenario_conventions`
  * :ref:`scenario_environment_configuration`
  * :ref:`scenario_ansible_configuration`

* **Custom/development repositories and packages:**

  * :ref:`tox_environment_variables`
