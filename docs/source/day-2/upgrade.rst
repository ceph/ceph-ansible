Upgrading the ceph cluster
--------------------------

ceph-ansible provides a playbook in ``infrastructure-playbooks`` for upgrading a Ceph cluster: ``rolling_update.yml``.

This playbook could be used for both minor upgrade (X.Y to X.Z) or major upgrade (X to Y).

Before running a major upgrade you need to update the ceph-ansible version first.

example:

.. code-block:: shell

   $ ansible-playbook -vv -i hosts infrastructure-playbooks/rolling_update.yml

.. note::
   This playbook isn't intended to be run with the ``--limit`` ansible option.