RBD Mirroring
=============

There's not so much to do from the primary cluster side in order to setup an RBD mirror replication.
``ceph_rbd_mirror_configure`` has to be set to ``true`` to make ceph-ansible create the mirrored pool
defined in ``ceph_rbd_mirror_pool`` and the keyring that is going to be used to add the rbd mirror peer.

group_vars from the primary cluster:

.. code-block:: yaml

      ceph_rbd_mirror_configure: true
      ceph_rbd_mirror_pool: rbd

Optionnally, you can tell ceph-ansible to set the name and the secret of the keyring you want to create:

.. code-block:: yaml

      ceph_rbd_mirror_local_user: client.rbd-mirror-peer  # 'client.rbd-mirror-peer' is the default value.
      ceph_rbd_mirror_local_user_secret: AQC+eM1iKKBXFBAAVpunJvqpkodHSYmljCFCnw==

This secret will be needed to add the rbd mirror peer from the secondary cluster.
If you do not enforce it as shown above, you can get it from a monitor by running the following command:
``ceph auth get {{ ceph_rbd_mirror_local_user }}``


.. code-block:: shell

    $ sudo ceph auth get client.rbd-mirror-peer

Once your variables are defined, you can run the playbook (you might want to run with --limit option):

.. code-block:: shell

    $ ansible-playbook -vv -i hosts site-container.yml --limit rbdmirror0


The configuration of the rbd mirror replication strictly speaking is done on the secondary cluster.
The rbd-mirror daemon pulls the data from the primary cluster. This is where the rbd mirror peer addition has to be done.
The configuration is similar with what was done on the primary cluster, it just needs few additional variables.

``ceph_rbd_mirror_remote_user`` : This user must match the name defined in the variable ``ceph_rbd_mirror_local_user`` from the primary cluster.
``ceph_rbd_mirror_remote_mon_hosts`` : This must a comma separated list of the monitor addresses from the primary cluster.
``ceph_rbd_mirror_remote_key`` : This must be the same value as the user (``{{ ceph_rbd_mirror_local_user }}``) keyring secret from the primary cluster.

group_vars from the secondary cluster:

.. code-block:: yaml

   ceph_rbd_mirror_configure: true
   ceph_rbd_mirror_pool: rbd
   ceph_rbd_mirror_remote_user: client.rbd-mirror-peer  # This must match the value defined in {{ ceph_rbd_mirror_local_user }} on primary cluster.
   ceph_rbd_mirror_remote_mon_hosts: 1.2.3.4
   ceph_rbd_mirror_remote_key: AQC+eM1iKKBXFBAAVpunJvqpkodHSYmljCFCnw==  # This must match the secret of the registered keyring of the user defined in {{ ceph_rbd_mirror_local_user }} on primary cluster.

Once you variables are defined, you can run the playbook (you might want to run with --limit option):

.. code-block:: shell

    $ ansible-playbook -vv -i hosts site-container.yml --limit rbdmirror0