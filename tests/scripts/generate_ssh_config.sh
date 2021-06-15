#!/bin/bash
# Generate a custom ssh config from Vagrant so that it can then be used by
# ansible.cfg 

path=$1

if [ $# -eq 0 ]
  then
    echo "A path to the scenario is required as an argument and it wasn't provided"
    exit 1
fi

cd "$path"

# Let's print vagrant status for debug purposes and to give the VMs a second to
# settle before asking vagrant for SSH config.
vagrant status || true

n=0
until [ "$n" -ge 5 ]
do
  vagrant ssh-config > vagrant_ssh_config && break
  n=$((n+1))
  echo "\`vagrant ssh-config\` failed.  Retrying."
  sleep 3
done

if [ "$n" -eq 5 ]; then
  echo "\`vagrant ssh-config\` failed 5 times.  This is a fatal error."
  cat vagrant_ssh_config
  exit 1
fi
