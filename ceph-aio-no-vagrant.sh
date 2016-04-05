#!/bin/bash
#
# This script will install Ansible and then deploy a simple Ceph cluster.
# The script relies on the auto osd discovery feature, so we at least expect 2 raw devices
# to work properly.
set -e

if [[ -z $1 ]]; then
  CEPH_BRANCH_DEFAULT=master
else
  CEPH_BRANCH_DEFAULT=$1
fi
CEPH_BRANCH=${CEPH_BRANCH:-$CEPH_BRANCH_DEFAULT}
SUBNET=$(ip r | grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}/[0-9]\{1,2\}' | head -1)
MON_IP=$(ip -4 -o a | awk '/eth/ { sub ("/..", "", $4); print $4 }')

if [[ $EUID -ne 0 ]]; then
    echo "You are NOT running this script as root."
    echo "You should."
    echo "Really."
    echo "PLEASE RUN IT WITH SUDO ONLY :)"
    exit 1
fi

sudo bash install-ansible.sh

ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
cat $HOME/.ssh/id_rsa.pub >> $HOME/.ssh/authorized_keys
cp group_vars/all.sample group_vars/all
cp group_vars/osds.sample group_vars/osds

sed -i "s/#osd_auto_discovery: false/osd_auto_discovery: true/" group_vars/osds
sed -i "s/#journal_collocation: false/journal_collocation: true/" group_vars/osds
sed -i "s/#ceph_dev: false/ceph_dev: true/" group_vars/all
sed -i "s/#pool_default_size: 3/pool_default_size: 2/" group_vars/all
sed -i "s/#monitor_address: 0.0.0.0/monitor_address: ${MON_IP}/" group_vars/all
sed -i "s/#journal_size: 0/journal_size: 100/" group_vars/all
sed -i "s|#public_network: 0.0.0.0\/0|public_network: ${SUBNET}|" group_vars/all
sed -i "s/#common_single_host_mode: true/common_single_host_mode: true/" group_vars/all
sed -i "s|#ceph_dev_branch: master|ceph_dev_branch: ${CEPH_BRANCH}|" group_vars/all

cat > /etc/ansible/hosts <<EOF
[mons]
localhost
[osds]
localhost
[mdss]
localhost
[rgws]
localhost
EOF

cp site.yml.sample site.yml
ansible all -m ping
ansible-playbook site.yml
