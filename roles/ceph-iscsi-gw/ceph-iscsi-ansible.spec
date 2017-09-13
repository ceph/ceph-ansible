Name:           ceph-iscsi-ansible
Version:        2.0
Release:        1%{?dist}
Summary:        Ansible playbooks for deploying LIO iscsi gateways in front of a Ceph cluster
License:        ASL 2.0
URL:            https://github.com/pcuzner/ceph-iscsi-ansible
Source0:        https://github.com/pcuzner/ceph-iscsi-ansible/archive/%{version}/%{name}-%{version}.tar.gz
BuildArch:      noarch

Requires: ansible >= 1.9
Requires: ceph-ansible >= 1.0.5

%description
Ansible playbooks that define nodes as iSCSI gateways (LIO). Once complete, the
LIO instance on each node provides an ISCSI endpoint for clients to connect to.
The playbook defines the front-end iSCSI environment (target -> tpgN ->
NodeACLS/client), as well as the underlying rbd definition for the rbd images
to be exported over iSCSI.

ceph-iscsi-gw.yml ......... defines the LIO configuration(defined by
                            group_vars/ceph-iscsi-gw.yml)
purge-iscsi-gateways.yml .. deletes the LIO configuration, and optionally rbd's
                            from the environment

NB: The playbooks are dependent upon the ceph-iscsi-config package being
installed/available to the hosts that will become iSCSI gateways.

%prep
%setup -q

%build

%install
mkdir -p %{buildroot}%{_datarootdir}/ceph-ansible

for f in group_vars library roles ceph-iscsi-gw.yml purge-iscsi-gateways.yml; do
  cp -a $f %{buildroot}%{_datarootdir}/ceph-ansible
done

%files
%doc LICENSE
%doc README
%{_datarootdir}/ceph-ansible/ceph-iscsi-gw.yml
%{_datarootdir}/ceph-ansible/purge-iscsi-gateways.yml
%{_datarootdir}/ceph-ansible/group_vars/ceph-iscsi-gw.sample
%{_datarootdir}/ceph-ansible/roles/ceph-iscsi-gw
%{_datarootdir}/ceph-ansible/library/igw*
%exclude %{_datarootdir}/ceph-ansible/library/igw*.pyo
%exclude %{_datarootdir}/ceph-ansible/library/igw*.pyc

%changelog
* Fri Jan 13 2017 Paul Cuzner <pcuzner@redhat.com> - 2.0-1
- converted from device-mapper/krbd to TCMU based rbd configurations
- renamed iscsi-gateway config file to use .cfg extension
- renamed purge playbook to match naming in ceph-ansible

* Fri Nov 04 2016 Paul Cuzner <pcuzner@redhat.com> - 1.5-1
- playbook now seeds the configuration directory on ansible host (rhbz 1390026)
- resolve a 1.4 regression affecting the igw_purge module
- fail gracefully if bogus client name is given (rhbz 1390023)

* Thu Oct 27 2016 Paul Cuzner <pcuzner@redhat.com> - 1.4-1
- clients can now be added without images or chap defined using null strings
- changed parameters for client definition to position for other auth mechanisms
- adapt purge module to use revised disk naming scheme within config object
- updated group_vars sample to reflect name changes
- added state= setting to LUN definitions (enabling disks to be add/removed)
- fix syntax issue during ceph.conf seed process
- documentation added to the Ansible modules

* Fri Oct 21 2016 Paul Cuzner <pcuzner@redhat.com> - 1.3-1
- removed rsync rpm dependency (BZ 1386090)
- ceph.conf pulled from seed monitor, then pushed to gateways using copy task
- add a template based config file to each gateway for runtime info
- add additional variables allowing non-default ceph cluster names/keyrings (BZ 1386617)

* Sat Oct 15 2016 Paul Cuzner <pcuzner@redhat.com> - 1.2-1
- documented the passwordless ssh requirement for the seed_monitor node
- fix BZ 1384505 mask the target service preventing manual start/stop
- fix BZ 1384858 when the admin updates ansible hosts but not the gateway_ip_list variable

* Wed Oct 12 2016 Paul Cuzner <pcuzner@redhat.com> - 1.1-1
- updated playbook to modify lvm.conf to exclude the dm devices created for mapped rbds

* Mon Oct 10 2016 Paul Cuzner <pcuzner@redhat.com> - 1.0-1
- fix : allow client_connections and rbd_devices to be be empty to skip those steps
- add usage guidelines to the group_vars/ceph-iscsi-gw.sample file
- added variable to allow pre-req checks to be bypassed during a run
- updated list of rpm pre-req that ansible checks for
- add synchronize task to the playbook to copy admin keyring to gateway node(s)
- updated igw_purge module to allow for the deletion of the alua port groups

* Thu Oct 06 2016 Paul Cuzner <pcuzner@redhat.com> - 0.8-1
- fix : purge_gateways.yml was missing
- removed packages directory to clean up the source archive
- spec file updates (dependencies)

* Wed Oct 05 2016 Paul Cuzner <pcuzner@redhat.com> - 0.7-1
- removed service dependencies for rbdmap/target (replaced by rbd-target-gw form ceph-iscsi-config rpm)
- removed target overrides files
- updated playbook to add skip_partx yes to multipath.conf

* Mon Oct 03 2016 Paul Cuzner <pcuzner@redhat.com> - 0.6-1
- changed the main function to have an ansible prefix to allow the code to know where it is invoked from
- updated the purge module to support image names being prefixed by a pool i.e. pool/image

* Tue Sep 27 2016 Paul Cuzner <pcuzner@redhat.com> - 0.5-1
- initial rpm package

