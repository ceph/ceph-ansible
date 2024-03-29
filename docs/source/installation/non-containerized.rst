Non containerized deployment
============================

The following are all of the available options for the installing Ceph through different channels.

We support 3 main installation methods, all managed by the ``ceph_origin`` variable:

- ``repository``: means that you will get Ceph installed through a new repository. Later below choose between ``community`` or ``dev``. These options will be exposed through the ``ceph_repository`` variable.
- ``distro``: means that no separate repo file will be added and you will get whatever version of Ceph is included in your Linux distro.
- ``local``: means that the Ceph binaries will be copied over from the local machine (not well tested, use at your own risk)

Origin: Repository
------------------

If ``ceph_origin`` is set to ``repository``, you now have the choice between a couple of repositories controlled by the ``ceph_repository`` option:

- ``community``: fetches packages from http://download.ceph.com, the official community Ceph repositories
- ``dev``: fetches packages from shaman, a gitbuilder based package system
- ``uca``: fetches packages from Ubuntu Cloud Archive
- ``custom``: fetches packages from a specific repository

Community repository
~~~~~~~~~~~~~~~~~~~~

If ``ceph_repository`` is set to ``community``, packages you will be by default installed from http://download.ceph.com, this can be changed by tweaking ``ceph_mirror``.


UCA repository
~~~~~~~~~~~~~~

If ``ceph_repository`` is set to ``uca``, packages you will be by default installed from http://ubuntu-cloud.archive.canonical.com/ubuntu, this can be changed by tweaking ``ceph_stable_repo_uca``.
You can also decide which OpenStack version the Ceph packages should come from by tweaking ``ceph_stable_openstack_release_uca``.
For example, ``ceph_stable_openstack_release_uca: queens``.

Dev repository
~~~~~~~~~~~~~~

If ``ceph_repository`` is set to ``dev``, packages you will be by default installed from https://shaman.ceph.com/, this can not be tweaked.
You can obviously decide which branch to install with the help of  ``ceph_dev_branch`` (defaults to 'main').
Additionally, you can specify a SHA1 with ``ceph_dev_sha1``, defaults to 'latest' (as in latest built).

Custom repository
~~~~~~~~~~~~~~~~~

If ``ceph_repository`` is set to ``custom``, packages you will be by default installed from a desired repository.
This repository is specified with ``ceph_custom_repo``, e.g: ``ceph_custom_repo: https://server.domain.com/ceph-custom-repo``.


Origin: Distro
--------------

If ``ceph_origin`` is set to ``distro``, no separate repo file will be added and you will get whatever version of Ceph is included in your Linux distro.


Origin: Local
-------------

If ``ceph_origin`` is set to ``local``, the ceph binaries will be copied over from the local machine (not well tested, use at your own risk)
