# ceph-iscsi-ansible
This project provides a mechanism to deploy iSCSI gateways in front of a ceph cluster using Ansible. The ansible playbooks  
provided rely upon configuration logic from the "ceph-iscsi-config" project. This separation provides independence to the   
configuration logic, potentially opening up the possibility for puppet/chef to create/manage ceph/iSCSI gateways in the  
same way.  

## Introduction
At a high level, this project provides custom modules which are responsible for calling the configuration logic, together  
with the relevant playbooks. The project defines a new ceph-ansible role; ceph-iscsi-gw, together with two playbooks;  

- **ceph-iscsi-gw-yml** ... to define our change the gateway configuration based on group_vars/ceph-iscsi-gw.yml  
- **purge_gateways.yml** .. to destroy the LIO configuration, or the LIO and any associated rbd images.

## Features    
The combination of the playbooks and the configuration logic deliver the following features;  

- confirms RHEL7.3 and aborts if necessary  
- ensures targetcli/device-mapper-multipath is installed (for rtslib support)  
- configures multipath.conf  
- creates rbd's if needed - at allocation time, each rbd is assigned an owner, which will become the preferred path    
- checks the size of the rbds at run time and expands if necessary  
- maps the rbd's to the host (gateway)  
- enables the rbdmap service to start on boot, and reconfigures the target service to be dependent on rbdmap  
- adds the rbd's to the /etc/ceph/rbdmap file ensuring the devices are automatically mapped following a gateway reboot  
- maps these rbds to LIO  
- once mapped, the alua preferred path state is set or cleared (supporting an active/passive topology)    
- creates an iscsi target - common iqn, and multiple tpg's  
- adds a portal ip based on a the provided IP addresses defined in the group vars to each tpg  
- enables the local tpg, other gateways are defined as disabled  
- adds all the mapped luns to ALL tpg's (ready for client assignment)  
- add clients to the active/enabled tpg, with/without CHAP  
- images mapped to clients can be added/removed by changing image_list and rerunning the playbook  
- clients can be removed using the state=absent variable and rerunning the playbook. At this point the entry can be  
  removed from the group variables file
- configuration can be wiped with the purge_gateway playbook  
- current state can be seen by looking at the configuration object (stored in the rbd pool)  

### Why RHEL 7.3?
There are several system dependencies that are required to ensure the correct (i.e. don't eat my data!) behaviors when OSD connectivity  
or gateway nodes fail. RHEL 7.3 delivers the necessary kernel changes, and also provides an updated multipathd, enabling rbd images  
to be managed by multipathd.

## Prerequisites  
* a working ceph cluster ( *rbd pool defined* )
* a server/host with ceph-ansible installed and working
* nodes intended to be gateways should be at least ceph clients, with the ability to create and map rbd images  
  

## Testing So far
The solution has been tested on a collocated cluster where the osd/mons and gateways all reside on the same node.  

## Quick Start
### Prepare the iSCSI Gateway Nodes  
1. install the ceph-iscsi-config package on the nodes, intended to be gateways. NB. The playbook includes a check for the presence  
 of this rpm (https://github.com/pcuzner/ceph-iscsi-config)

### Install the ansible playbooks
1. install the ceph-iscsi-ansible rpm from the packages directory on the node where you already have ceph-ansible installed.  
2. update /etc/ansible/hosts to include a host group (ceph-iscsi-gw) for the nodes that you want to become iscsi gateways  
3. make a copy of the group_vars/ceph-iscsi-gw.sample file called ceph-iscsi-gw, and update it to define the environment you want  
4. run the playbook  
  ```> ansible-playbook ceph-iscsi-gw.yml```
  
## Purging the configuration
As mentioned above, the project provides a purge-gateways.yml playbook which can remove the LIO configuration alone, or remove   
both LIO and all associated rbd images that have been declared in the group_vars/ceph-iscsi-gw file. The purge playbook will  
check for any active iscsi sessions, and abort if any are found.
    
## Known Issues and Considerations  
1. the ceph cluster name is the default 'ceph', so the corresponding configuration file /etc/ceph/ceph.conf is assumed to be valid