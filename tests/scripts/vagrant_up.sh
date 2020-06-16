#!/bin/bash

vagrant box remove --provider libvirt --box-version 1905.1 centos/8 || true
vagrant box add --provider libvirt --name centos/8 https://cloud.centos.org/centos/8/vagrant/x86_64/images/CentOS-8-Vagrant-8.2.2004-20200611.2.x86_64.vagrant-libvirt.box || true

retries=0
until [ $retries -ge 5 ]
do
  echo "Attempting to start VMs. Attempts: $retries"
  timeout 10m time vagrant up "$@" && break
  retries=$[$retries+1]
  sleep 5
done

sleep 10