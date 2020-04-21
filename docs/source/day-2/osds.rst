Adding/Removing OSD(s) after a cluster is deployed is a common operation that should be straight-forward to achieve.


Adding osd(s)
-------------

Adding new OSD(s) on an existing host or adding a new OSD node can be achieved by running the main playbook with the ``--limit`` ansible option.
You basically need to update your host_vars/group_vars with the new hardware and/or the inventory host file with the new osd nodes being added.

The command used would be like following:

``ansible-playbook -vv -i <your-inventory> site-docker.yml --limit <node>``

example:

.. code-block:: shell

   $ cat hosts
   [mons]
   mon-node-1
   mon-node-2
   mon-node-3

   [mgrs]
   mon-node-1
   mon-node-2
   mon-node-3

   [osds]
   osd-node-1
   osd-node-2
   osd-node-3
   osd-node-99
   
   $ ansible-playbook -vv -i hosts site-docker.yml --limit osd-node-99


Shrinking osd(s)
----------------

Shrinking OSDs can be done by using the shrink-osd.yml playbook provided in ``infrastructure-playbooks`` directory.

The variable ``osd_to_kill`` is a comma separated list of OSD IDs which must be passed to the playbook (passing it as an extra var is the easiest way).

The playbook will shrink all osds passed in ``osd_to_kill`` serially.

example:

.. code-block:: shell

   $ ansible-playbook -vv -i hosts infrastructure-playbooks/shrink-osds.yml -e osd_to_kill=1,2,3