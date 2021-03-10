Installation methods
====================

ceph-ansible can deploy Ceph either in a non-containerized context (via packages) or in a containerized context using ceph-container images.

.. toctree::
   :maxdepth: 1

   non-containerized
   containerized

The difference here is that you don't have the rbd command on the host when using the containerized deployment so everything related to ceph needs to be executed within a container. So in the case there is software like e.g. Open Nebula which requires that the rbd command is accessible directly on the host (non-containerized) then you have to install the rbd command by yourself on those servers outside of containers (or make sure that this software somehow runs within containers as well and that it can access rbd).
