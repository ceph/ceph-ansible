.. _molecule_testing:

Testing with Molecule
=====================

``ceph-ansible`` uses `Molecule <https://ansible.readthedocs.io/projects/molecule/>`_
with the Docker driver (configured in ``tox-molecule.ini``) as the primary way to
run functional cluster tests locally and in GitHub Actions CI.

.. note::

   The older Vagrant / VirtualBox / libvirt harness (``tox.ini``, see
   :doc:`running`) is deprecated.


Prerequisites
-------------

* A running Docker daemon on Linux (Molecule starts privileged systemd
  containers and creates loop/LVM devices for OSDs).
* ``tox`` (recommended) or a Python virtualenv with ``tests/requirements.txt``
  and ``ansible-core`` installed.
* Sufficient host resources for 4 cluster nodes running MON, MGR, OSD, MDS,
  and RGW daemons simultaneously:

  * **CPU / Memory:** At least 4 vCPUs and 8–16 GB RAM recommended (especially
    for ``molecule-container`` and ``molecule-switch-to-containers``).
  * **Disk space:** OSD backing files are sparse, so they only consume space
    as data is written, plus a few GB for OS/Ceph packages or container images.
    However, ensure the filesystem backing Docker (``/var/lib/docker``) has
    **more than 30% free space** — Ceph monitors warn with ``MON_DISK_LOW``
    below ``mon_data_avail_warn`` (default ``30%``), which will fail cluster
    health checks during ``verify``.

.. warning::

   To simulate OSD disks, Molecule creates sparse files backed by loop devices
   and configures LVM volumes on them. Because the test containers run in
   Docker ``privileged`` mode and share udev/device-mapper with the host
   kernel, those loop and LVM devices propagate to the host machine. While
   Molecule's ``cleanup`` playbook removes the volume groups, physical volumes,
   and loop devices when a run finishes (or if ``molecule cleanup`` is run
   manually), it is still recommended to run Molecule tests inside a dedicated
   VM or disposable environment rather than on a production or primary
   workstation.


Available scenarios
-------------------

The Molecule scenarios are defined under ``molecule/`` and exposed as ``tox``
environments in ``tox-molecule.ini``:

* ``molecule-all-in-one`` (``molecule test -s all_in_one``):
  Deploys a **non-containerized** Ceph cluster using native OS packages and
  systemd services across 4 simulated host nodes (``osd0``–``osd2`` with
  collocated ``mons``, ``mgrs``, ``osds``, ``mdss``, and ``rgws``, plus
  ``osd3`` as a spare node). It verifies idempotence and cluster health, then
  exercises scaling/shrinking daemons (RGW, MDS, OSD, MGR, and MON) on
  ``osd3`` via ``side_effect`` and ``verify_shrink.yml``.


* ``molecule-container`` (``molecule test -s container``):
  Deploys a containerized Ceph cluster (using ``quay.io/ceph/ceph`` images by
  default), verifies idempotence, and validates cluster health and versions.

* ``molecule-switch-to-containers`` (``molecule test -s switch_to_containers``):
  Deploys a non-containerized cluster in ``prepare``, runs
  ``infrastructure-playbooks/switch-from-non-containerized-to-containerized-ceph-daemons.yml``
  in ``converge``, and verifies both cluster health and that no Ceph daemons
  remain running on the host outside containers.

* ``molecule-upgrade`` (``molecule test -s upgrade``):
  Deploys an initial Ceph release using the N-1 branch and upgrades it to the
  target release with ``infrastructure-playbooks/rolling_update.yml``.

* ``molecule-rbdmirror`` (``molecule test -s rbdmirror``):
  Deploys primary and secondary clusters and verifies ``ceph-rbd-mirror``
  daemon and pool mirroring functionality.


Running a scenario with tox
---------------------------

Run any scenario end-to-end using ``tox-molecule.ini``:

.. code-block:: console

   tox -c tox-molecule.ini -e molecule-all-in-one

To run the containerized or switch-to-containers scenarios:

.. code-block:: console

   tox -c tox-molecule.ini -e molecule-container
   tox -c tox-molecule.ini -e molecule-switch-to-containers


Iterative development with molecule
-----------------------------------

If you already have a ``tox`` environment created (for example under
``.tox/molecule-all-in-one``) or have ``molecule`` installed in your virtualenv,
you can run individual Molecule stages instead of the full ``test`` matrix:

.. code-block:: console

   # Prepare containers and LVM/loop devices
   molecule create -s container
   molecule prepare -s container

   # Run the playbook and re-run to iterate on changes
   molecule converge -s container

   # Run verification playbooks
   molecule verify -s container

   # Clean up loop devices, LVM, and containers
   molecule cleanup -s container
   molecule destroy -s container


.. _molecule_env_vars:

Environment variables
---------------------

``tox-molecule.ini`` passes the following environment variables through to
Molecule and Ansible:

* ``DOCKER_REGISTRY``: Container registry for the systemd test node image
  (default: ``quay.io/gotmax23``).
* ``DOCKER_IMAGE_TAG``: Distribution image and tag for the test nodes
  (default: ``debian-systemd:bookworm``; CI also tests e.g.
  ``ubuntu-systemd:noble``, ``centos-systemd:stream10``,
  ``rockylinux-systemd:10``).
* ``DOCKER_COMMAND``: Optional command override for the systemd test container.
* ``CEPH_REPOSITORY``: Ceph repository type (e.g. ``community`` or ``dev``).
* ``CEPH_STABLE_RELEASE``: Target Ceph release name (e.g. ``squid``,
  ``tentacle``, ``umbrella``).
* ``ANSIBLE_VERSION``: ``ansible-core`` minor version installed in the tox
  environment (default: ``2.21``).
* ``CEPH_INITIAL_RELEASE`` / ``CEPH_TARGET_RELEASE`` / ``CEPH_ANSIBLE_N1_BRANCH`` / ``CEPH_ANSIBLE_N1_PATH``:
  Used by ``molecule-upgrade`` to configure the source release, target release,
  and N-1 ``ceph-ansible`` checkout.

Example running ``all_in_one`` on Ubuntu Noble with Ceph Tentacle:

.. code-block:: console

   DOCKER_IMAGE_TAG=ubuntu-systemd:noble \
   CEPH_REPOSITORY=community \
   CEPH_STABLE_RELEASE=tentacle \
   tox -c tox-molecule.ini -e molecule-all-in-one


.. _molecule_layout:

Scenario layout and structure
-----------------------------

Molecule scenarios live under ``molecule/<scenario>/`` and share common
playbooks from ``molecule/default/`` as well as inventory ``group_vars`` from
``tests/functional/all-in-one/group_vars/``:

.. code-block:: none

   molecule/
   ├── default/                  # Shared prepare.yml, converge.yml, cleanup.yml
   ├── all_in_one/               # Non-containerized deploy + extend/shrink side_effect
   ├── container/                # Containerized deploy (site-container.yml.sample)
   ├── switch_to_containers/     # Bare-metal prepare -> switch playbook -> verify
   ├── upgrade/                  # N-1 release prepare -> rolling_update.yml -> verify
   └── rbdmirror/                # Primary/secondary cluster + rbd-mirror side_effect

Each scenario directory typically contains:

* ``molecule.yml``: Defines the Docker ``platforms`` (node names, Ansible
  groups, systemd image, networks, mounts), ``provisioner`` playbooks and
  ``--extra-vars``, and ``scenario.test_sequence``.
* ``extra_vars.yml``: Scenario-specific Ansible variables passed via
  ``--extra-vars``.
* Optional stage playbooks (``prepare.yml``, ``converge.yml``,
  ``side_effect.yml``, ``verify.yml``, ``cleanup.yml``) whenever a scenario
  needs behavior beyond the shared ``molecule/default/`` playbooks.


.. _molecule_verification:

Ansible-based verification tests
--------------------------------

Functional cluster tests have been **migrated from Python (``pytest`` /
``testinfra``) to Ansible playbooks** under ``tests/functional/molecule/``.
(Python ``pytest`` is still used for unit tests of custom Ansible modules under
``tests/library/``.)

.. code-block:: none

   tests/functional/molecule/
   ├── verify.yml           # Main verification entrypoint
   ├── gather_facts.yml     # Collects packages, services, ceph status, ceph versions
   ├── check_install.yml    # Verifies installed packages, configs, and keyrings
   ├── check_mon.yml        # Verifies MON quorum, min_mon_release_name, ceph versions
   ├── check_mgr.yml        # Verifies active/standby MGR daemons
   ├── check_osd.yml        # Verifies OSD services, up/in counts, PGs, and CRUSH tree
   ├── check_mds.yml        # Verifies MDS services and fsmap state
   ├── check_rgw.yml        # Verifies RGW services, listening ports, and servicemap
   ├── check_rbdmirror.yml  # Verifies rbd-mirror services and mirroring state
   └── verify_shrink.yml    # Verifies cluster state after daemon shrinkage

When writing verification checks:

* Add general daemon or cluster health assertions to the corresponding
  ``tests/functional/molecule/check_<daemon>.yml`` task file so all scenarios
  benefit automatically.
* For scenario-specific checks, create a local ``molecule/<scenario>/verify.yml``
  that imports ``../../tests/functional/molecule/verify.yml`` and appends extra
  plays (see ``molecule/switch_to_containers/verify.yml`` for an example).


.. _molecule_adding_scenario:

Adding a new Molecule scenario
------------------------------

1. Create ``molecule/<scenario>/molecule.yml`` and ``extra_vars.yml``, reusing
   ``../default/prepare.yml``, ``../default/converge.yml``,
   ``../default/cleanup.yml``, and ``../../tests/functional/molecule/verify.yml``
   where possible.
2. Add any custom stage playbooks (such as ``converge.yml``,
   ``side_effect.yml``, or ``verify.yml``) in ``molecule/<scenario>/``.
3. Register a new ``[testenv:molecule-<name>]`` environment in
   ``tox-molecule.ini`` and add it to ``envlist``.
4. If the scenario should run in CI, add a job or matrix entry in
   ``.github/workflows/molecule.yml``.
5. Validate locally with ``molecule syntax -s <scenario>`` and
   ``tox -c tox-molecule.ini -e molecule-<name>``.
