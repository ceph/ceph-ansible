#!/bin/bash
#
# THIS SCRIPT INSTALLS ANSIBLE
set -e

if [[ $EUID -ne 0 ]]; then
    echo "You are NOT running this script as root."
    echo "You should."
    echo "Really."
    exit 1
fi

if [[ ! -x $(which lsb_release 2>/dev/null) ]]; then
  echo "ERROR: lsb_release is not installed"
  echo "Can not evaluate the platform"
  echo "Please install lsb_release and retry"
  echo "Red Hat based Systems : yum install redhat-lsb-core"
  echo "Debian based Systems : apt-get install lsb-release"
  exit 1
fi
 

# GET OS VENDOR
os_VENDOR=$(lsb_release -i -s)
# GET OS MAJOR VERSION
os_VERSION=$(lsb_release  -r  -s | cut -d. -f 1)


if [[ "Debian" =~ $os_VENDOR ]]; then
  apt-get update
  apt-get install -y python-pip python-dev git build-essential
  pip install PyYAML jinja2 paramiko
  git clone https://github.com/ansible/ansible.git
  cd ansible
  make install
  mkdir /etc/ansible
elif [[ "Ubuntu" =~ $os_VENDOR || "LinuxMint" =~ $os_VENDOR ]]; then
  add-apt-repository -y ppa:ansible/ansible
  apt-get update
  apt-get install -y ansible
elif [[ "RedHatEnterpriseServer" =~ $os_VENDOR || "CentOS" =~ $os_VENDOR || -r /etc/redhat-release ]]; then
  rpm -q epel-release-* || rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-${os_VERSION}.noarch.rpm
  yum install -y ansible
  yum remove -y $(rpm -q epel-release-*)
else
  echo "Unsupported platform ${os_VENDOR}: ${os_VERSION}"
  echo "Please send a pull-request or open an issue"
  echo "on https://github.com/ceph/ceph-ansible/"
  exit 1
fi
