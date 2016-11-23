#!/bin/bash
#
# This script will install Ansible and then deploy a simple Ceph cluster.
# The script relies on the auto osd discovery feature, so we at least expect 2 raw devices
# to work properly.
set -e


# VARIABLES

SOURCE=stable
IP=$(ip -4 -o a | awk '/eth|ens|eno|enp|em|p.p./ { sub ("/..", "", $4); print $4 }' | head -1)
SUBNET=$(ip r | grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}/[0-9]\{1,2\}' | head -1)


# FUNCTIONS

show_help() {
    PROG=$(basename $0)
    echo ""
    echo "Usage of ${PROG}:"
    cat << EOF

None of the following options are mandatory!

-h                 : HELP, show this help & exit
-s stable          : INSTALL SOURCE, valid values are 'stable' or 'dev' (DEFAULT: stable)
-b master          : DEV BRANCH, only valid when '-s dev' (DEFAULT: master)
-i 192.168.0.1     : IP, if not set the first IP of the stack will be used
-n 192.168.0.0/24  : Subnet, if not set the first subnet of the stack will be used

Examples:
${PROG} -s stable # installs latest stable version and detects IP/SUBNET
${PROG} -s stable -i 192.168.0.1 -n 192.168.0.0/24 # installs latest stable version and use the provided IP/SUBNET
${PROG} -s dev -b master # installs master branch version and detects IP/SUBNET
${PROG} -s dev -b master -i 192.168.0.1 -n 192.168.0.0/24 # installs master branch version and use the provided IP/SUBNET
EOF
}

parse_cmdline() {
while getopts "hs:b:i:n:" opt; do
  case $opt in
    h)
    show_help
    exit 0
    ;;
    s)
    SOURCE=${OPTARG}
    ;;
    b)
    BRANCH=${OPTARG}
    ;;
    i)
    IP=${OPTARG}
    ;;
    n)
    SUBNET=${OPTARG}
    ;;
   \?)
      exit 1
    ;;
    : )
      exit 1
    ;;
  esac
done

if [ $# -eq 0 ]; then
  show_help
  exit 0
fi

if [[ ${SOURCE} == 'stable' && ! -z ${BRANCH} ]]; then
  echo "You can not use a stable install source and a specific branch!"
  echo "A branch can be specified when a 'dev' source is desired".
  echo "Run the script with -h for examples."
  exit 1
fi

}

function install_ansible {
  sudo bash install-ansible.sh
}

function ssh_setup {
  echo -e  'y\n'|ssh-keygen -q -t rsa -N "" -f ~/.ssh/id_rsa
  cat $HOME/.ssh/id_rsa.pub >> $HOME/.ssh/authorized_keys
}

function cp_var {
  cp group_vars/all.yml.sample group_vars/all.yml
  cp group_vars/osds.yml.sample group_vars/osds.yml
  cp site.yml.sample site.yml
}

function populate_vars {
  sed -i "s/#osd_auto_discovery: false/osd_auto_discovery: true/" group_vars/osds.yml
  sed -i "s/#journal_collocation: false/journal_collocation: true/" group_vars/osds.yml
  sed -i "s/#pool_default_size: 3/pool_default_size: 2/" group_vars/all.yml
  sed -i "s/#monitor_address: 0.0.0.0/monitor_address: ${IP}/" group_vars/all.yml
  sed -i "s/#journal_size: 0/journal_size: 100/" group_vars/all.yml
  sed -i "s|#public_network: 0.0.0.0\/0|public_network: ${SUBNET}|" group_vars/all.yml
  sed -i "s/#common_single_host_mode: true/common_single_host_mode: true/" group_vars/all.yml
  if [[ ${SOURCE} == 'stable' ]]; then
    sed -i "s/#ceph_stable: false/ceph_stable: true/" group_vars/all.yml
  else
    sed -i "s/#ceph_dev: false/ceph_dev: true/" group_vars/all.yml
    sed -i "s|#ceph_dev_branch: master|ceph_dev_branch: ${BRANCH}|" group_vars/all.yml
  fi
}

function create_inventory {
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
}

function test_and_run {
  ansible all -m ping
  ansible-playbook site.yml
}


# MAIN
parse_cmdline $@
install_ansible
ssh_setup
cp_var
populate_vars
create_inventory
test_and_run
