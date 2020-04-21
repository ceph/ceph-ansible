Purging the cluster
-------------------

ceph-ansible provides two playbooks in ``infrastructure-playbooks`` for purging a Ceph cluster: ``purge-cluster.yml`` and ``purge-docker-cluster.yml``.

The names are pretty self-explanatory, ``purge-cluster.yml`` is intended to purge a non-containerized cluster whereas ``purge-docker-cluster.yml`` is to purge a containerized cluster.

example:

.. code-block:: shell

   $ ansible-playbook -vv -i hosts infrastructure-playbooks/purge-docker-cluster.yml

.. note::
   These playbooks aren't intended to be run with the ``--limit`` option.