.. _testing:

Testing
=======

``ceph-ansible`` has the ability to test different scenarios (collocated journals
or dmcrypt OSDs for example) in an isolated, repeatable, and easy way.

Tests are run locally and in CI using :doc:`Molecule <molecule>` with Docker.

.. warning::

   The Vagrant / VirtualBox / libvirt test harness (``tox.ini``) is
   **deprecated** in favor of :doc:`Testing with Molecule <molecule>`
   (``tox-molecule.ini``).

* **Getting started:**

  * :doc:`Testing with Molecule <molecule>`
  * :ref:`molecule_env_vars`
  * :ref:`molecule_layout`
  * :ref:`molecule_verification`
  * :ref:`molecule_adding_scenario`

* **Legacy Vagrant / testinfra (deprecated):**

  * :doc:`Running a Test Scenario (Legacy Vagrant) <running>`
  * :ref:`tox_environment_variables`
  * :ref:`dependencies`
  * :ref:`layout`
  * :ref:`test_files`
  * :ref:`scenario_files`
  * :ref:`scenario_wiring`
  * :ref:`test_conventions`
  * :ref:`testinfra`
  * :ref:`scenario_conventions`
  * :ref:`scenario_environment_configuration`
  * :ref:`scenario_ansible_configuration`
