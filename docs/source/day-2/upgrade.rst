Upgrading the ceph cluster
--------------------------

ceph-ansible provides a playbook in ``infrastructure-playbooks`` for upgrading a Ceph cluster: ``rolling_update.yml``.

This playbook could be used for both minor upgrades (X.Y to X.Z) or major upgrades (X to Y).

Before running a major upgrade you need to update the ceph-ansible version first.

example:

.. code-block:: shell

   $ ansible-playbook -vv -i hosts infrastructure-playbooks/rolling_update.yml

.. note::
   You can use the ``--limit`` flag with the rolling-update playbook to target
   a subset of OSDs or mons. For example::

      ansible-playbook -vv -i hosts infrastructure-playbooks/rolling_update.yml \
         --limit mon1 --tags=mons
