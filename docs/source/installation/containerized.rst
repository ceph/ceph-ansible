Containerized deployment
========================

Ceph-ansible supports docker and podman only in order to deploy Ceph in a containerized context.

Configuration and Usage
-----------------------

To deploy ceph in containers, you will need to set the ``containerized_deployment`` variable to ``true`` and use the site-container.yml.sample playbook.

.. code-block:: yaml

   containerized_deployment: true

The ``ceph_origin`` and ``ceph_repository`` variables aren't needed anymore in containerized deployment and are ignored.

.. code-block:: console

   $ ansible-playbook site-container.yml.sample

.. note::

   The infrastructure playbooks are working for both non containerized and containerized deployment.

Custom container image
----------------------

You can configure your own container register, image and tag by using the ``ceph_docker_registry``, ``ceph_docker_image`` and ``ceph_docker_image_tag`` variables.

.. code-block:: yaml

   ceph_docker_registry: quay.ceph.io
   ceph_docker_image: ceph-ci/daemon
   ceph_docker_image_tag: latest

.. note::

   ``ceph_docker_image`` should have both image namespace and image name concatenated and separated by a slash character.

   ``ceph_docker_image_tag`` should be set to a fixed tag, not to any "latest" tags unless you know what you are doing. Using a "latest" tag
   might make the playbook restart all the daemons deployed in your cluster since these tags are intended to be updated periodically.

Container registry authentication
---------------------------------

When using a container registry with authentication then you need to set the ``ceph_docker_registry_auth`` variable to ``true`` and provide the credentials via the
``ceph_docker_registry_username`` and ``ceph_docker_registry_password`` variables

.. code-block:: yaml

   ceph_docker_registry_auth: true
   ceph_docker_registry_username: foo
   ceph_docker_registry_password: bar

Container registry behind a proxy
---------------------------------

When using a container registry reachable via a http(s) proxy then you need to set the ``ceph_docker_http_proxy`` and/or ``ceph_docker_https_proxy`` variables. If you need
to exclude some host for the proxy configuration to can use the ``ceph_docker_no_proxy`` variable.

.. code-block:: yaml

   ceph_docker_http_proxy: http://192.168.42.100:8080
   ceph_docker_https_proxy: https://192.168.42.100:8080