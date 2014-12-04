#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "You are NOT running this script as root."
    echo "You should."
    echo "Really."
    exit 1
fi

if [[ -x $(which lsb_release 2>/dev/null) ]]; then
  os_VENDOR=$(lsb_release -i -s)
  os_VERSION=$(lsb_release -c -s)
  if [[ "Debian" =~ $os_VENDOR ]]; then
    apt-get update
    apt-get install python-pip python-dev git build-essential -y
    pip install PyYAML jinja2 paramiko
    git clone https://github.com/ansible/ansible.git
    cd ansible
    make install
    mkdir /etc/ansible
  elif [[ "Ubuntu" =~ $os_VENDOR ]]; then
    if [[ "precise" =~ $os_VERSION ]]; then
      add-apt-repository ppa:rquillo/ansible
      apt-get update
      apt-get install -y ansible
    else
      apt-get install -y ansible
    fi
  fi
elif [[ -r /etc/redhat-release ]]; then
  yum install -y ansible
fi
