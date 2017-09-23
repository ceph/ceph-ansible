#!/bin/bash
#
# This script will install Ansible and then deploy a simple Ceph cluster.
# The script relies on the auto osd discovery feature
set -e


# VARIABLES

SOURCE=stable
IP=$(ip -4 -o a | awk '/eth|ens|eno|enp|em|p.p./ { sub ("/..", "", $4); print $4 }' | head -1)
SUBNET=$(ip r | grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}/[0-9]\{1,2\}' | head -1)
CEPH_POOL_DEFAULT_SIZE=2
INSTALL_MDS=true
INSTALL_RGW=true


# FUNCTIONS

show_help() {
    PROG=$(basename "$0")
    echo ""
    echo "Usage of ${PROG}:"
    cat << EOF

None of the following options are mandatory!

-h                 : HELP, show this help & exit
-s stable          : INSTALL SOURCE, valid values are 'stable' or 'dev' (DEFAULT: stable)
-b master          : DEV BRANCH, only valid when '-s dev' (DEFAULT: master)
-i 192.168.0.1     : IP, if not set the first IP of the stack will be used
-n 192.168.0.0/24  : Subnet, if not set the first subnet of the stack will be used
-p 2               : OSD default pool size and min_size (DEFAULT: 2)
-m true            : Install MDS (DEFAULT: true)
-r true            : Install RGW (DEFAULT: true)

Examples:
${PROG} -s stable # installs latest stable version and detects IP/SUBNET
${PROG} -s stable -i 192.168.0.1 -n 192.168.0.0/24 # installs latest stable version and use the provided IP/SUBNET
${PROG} -s dev -b master # installs master branch version and detects IP/SUBNET
${PROG} -s dev -b master -i 192.168.0.1 -n 192.168.0.0/24 # installs master branch version and use the provided IP/SUBNET
${PROG} -s stable -i 192.168.0.1 -n 192.168.0.0/24 -p 1 -m false -r false # install latest stable version, use the provided IP/SUBNET, set default pool size and min_size to 1 and don't install MDS and RGW
EOF
}

parse_cmdline() {
while getopts "hs:b:i:n:p:m:r:" opt; do
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
    p)
    CEPH_POOL_DEFAULT_SIZE=${OPTARG}
    ;;
    m)
    INSTALL_MDS=${OPTARG}
    ;;
    r)
    INSTALL_RGW=${OPTARG}
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

function is_ansible_installed {
  if ! command -v ansible-playbook 1&> /dev/null; then
    echo "Please install Ansible"
    exit 1
  fi
}

function ssh_setup {
  if [ ! -f "$HOME"/.ssh/id_rsa ]; then
    echo -e  'y\n'|ssh-keygen -q -t rsa -N "" -f "$HOME"/.ssh/id_rsa
  fi
  if ! grep -Fxq "$(cat "$HOME"/.ssh/id_rsa.pub)" "$HOME"/.ssh/authorized_keys; then
    cat "$HOME"/.ssh/id_rsa.pub >> "$HOME"/.ssh/authorized_keys
  fi
}

function cp_var {
  cp group_vars/all.yml.sample group_vars/all.yml
  cp group_vars/osds.yml.sample group_vars/osds.yml
  cp site.yml.sample site.yml
}

function populate_vars {
  sed -i "s/[#]*osd_auto_discovery: .*/osd_auto_discovery: true/" group_vars/osds.yml
  sed -i "s/[#]*osd_scenario: .*/osd_scenario: collocated/" group_vars/osds.yml
  sed -i "s/[#]*monitor_address: .*/monitor_address: ${IP}/" group_vars/all.yml
  sed -i "s/[#]*journal_size: .*/journal_size: 100/" group_vars/all.yml
  sed -i "s|[#]*public_network: .*|public_network: ${SUBNET}|" group_vars/all.yml
  sed -i "s/[#]*common_single_host_mode: .*/common_single_host_mode: true/" group_vars/all.yml

  if ! grep -q '^ceph_conf_overrides:' group_vars/all.yml; then
    cat >> group_vars/all.yml <<EOF
ceph_conf_overrides:
  global:
    mon pg warn max per osd: 0
    osd pool default size: 2
EOF
  fi
  sed -i "s/^    osd pool default size: .*/    osd pool default size: $CEPH_POOL_DEFAULT_SIZE/" group_vars/all.yml

  if [[ ${SOURCE} == 'stable' ]]; then
    sed -i "s/[#]*ceph_stable: .*/ceph_stable: true/" group_vars/all.yml
  else
    sed -i "s/[#]*ceph_dev: .*/ceph_dev: true/" group_vars/all.yml
    sed -i "s|[#]*ceph_dev_branch: .*|ceph_dev_branch: ${BRANCH}|" group_vars/all.yml
  fi
}

function create_inventory {
  cat > hosts <<EOF
[mons]
localhost
[osds]
localhost
EOF
  if [ "$INSTALL_MDS" = true ] ; then
    cat >> hosts <<EOF
[mdss]
localhost
EOF
  fi
  if [ "$INSTALL_RGW" = true ] ; then
    cat >> hosts <<EOF
[rgws]
localhost
EOF
  fi
}

function test_and_run {
  ANSIBLE_HOST_KEY_CHECKING=False ansible all -i hosts -m ping
  ansible-playbook -i hosts site.yml
}


# MAIN
parse_cmdline $@
is_ansible_installed
ssh_setup
cp_var
populate_vars
create_inventory
test_and_run
