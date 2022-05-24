.. _tox:

``tox``
=======

``tox`` is an automation project we use to run our testing scenarios. It gives us
the ability to create a dynamic matrix of many testing scenarios, isolated testing environments
and a provides a single entry point to run all tests in an automated and repeatable fashion.

Documentation for tox can be found `here <https://tox.readthedocs.io/en/latest/>`_.


.. _tox_environment_variables:

Environment variables
---------------------

When running ``tox`` we've allowed for the usage of environment variables to tweak certain settings
of the playbook run using Ansible's ``--extra-vars``. It's helpful in Jenkins jobs or for manual test
runs of ``ceph-ansible``.

The following environent variables are available for use:

* ``CEPH_DOCKER_REGISTRY``: (default: ``quay.ceph.io``) This would configure the ``ceph-ansible`` variable ``ceph_docker_registry``.

* ``CEPH_DOCKER_IMAGE``: (default: ``ceph-ci/daemon``) This would configure the ``ceph-ansible`` variable ``ceph_docker_image``.

* ``CEPH_DOCKER_IMAGE_TAG``: (default: ``latest``) This would configure the ``ceph-ansible`` variable ``ceph_docker_image_name``.

* ``CEPH_DEV_BRANCH``: (default: ``main``) This would configure the ``ceph-ansible`` variable ``ceph_dev_branch`` which defines which branch we'd
  like to install from shaman.ceph.com.

* ``CEPH_DEV_SHA1``: (default: ``latest``) This would configure the ``ceph-ansible`` variable ``ceph_dev_sha1`` which defines which sha1 we'd like
  to install from shaman.ceph.com.

* ``UPDATE_CEPH_DEV_BRANCH``: (default: ``main``) This would configure the ``ceph-ansible`` variable ``ceph_dev_branch`` which defines which branch we'd
  like to update to from shaman.ceph.com.

* ``UPDATE_CEPH_DEV_SHA1``: (default: ``latest``) This would configure the ``ceph-ansible`` variable ``ceph_dev_sha1`` which defines which sha1 we'd like
  to update to from shaman.ceph.com.


.. _tox_sections:

Sections
--------

The ``tox.ini`` file has a number of top level sections defined by ``[ ]`` and subsections within those. For complete documentation
on all subsections inside of a tox section please refer to the tox documentation.

* ``tox`` : This section contains the ``envlist`` which is used to create our dynamic matrix. Refer to the `section here <http://tox.readthedocs.io/en/latest/config.html#generating-environments-conditional-settings>`_ for more information on how the ``envlist`` works. 

* ``purge`` : This section contains commands that only run for scenarios that purge the cluster and redeploy. You'll see this section being reused in ``testenv``
  with the following syntax: ``{[purge]commands}``

* ``update`` : This section contains commands taht only run for scenarios that deploy a cluster and then upgrade it to another Ceph version.

* ``testenv`` : This is the main section of the ``tox.ini`` file and is run on every scenario. This section contains many *factors* that define conditional
  settings depending on the scenarios defined in the ``envlist``. For example, the factor ``centos7_cluster`` in the ``changedir`` subsection of ``testenv`` sets
  the directory that tox will change do when that factor is selected. This is an important behavior that allows us to use the same ``tox.ini`` and reuse commands while
  tweaking certain sections per testing scenario.


.. _tox_environments:

Modifying or Adding environments
--------------------------------

The tox environments are controlled by the ``envlist`` subsection of the ``[tox]`` section. Anything inside of ``{}`` is considered a *factor* and will be included
in the dynamic matrix that tox creates. Inside of ``{}`` you can include a comma separated list of the *factors*. Do not use a hyphen (``-``) as part
of the *factor* name as those are used by tox as the separator between different factor sets.

For example, if wanted to add a new test *factor* for the next Ceph release of luminious this is how you'd accomplish that. Currently, the first factor set in our ``envlist``
is used to define the Ceph release (``{jewel,kraken,rhcs}-...``). To add luminous you'd change that to look like ``{luminous,kraken,rhcs}-...``. In the ``testenv`` section
this is a subsection called ``setenv`` which allows you to provide environment variables to the tox environment and we support an environment variable called ``CEPH_STABLE_RELEASE``. To ensure that all the new tests that are created by adding the luminous *factor* you'd do this in that section: ``luminous: CEPH_STABLE_RELEASE=luminous``.
