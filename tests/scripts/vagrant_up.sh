#!/bin/bash

vagrant box remove --force --provider libvirt --box-version 0 centos/stream8 || true
vagrant box add --provider libvirt --name centos/stream8 https://cloud.centos.org/centos/8-stream/x86_64/images/CentOS-Stream-Vagrant-8-20220125.1.x86_64.vagrant-libvirt.box || true

retries=0
until [ $retries -ge 5 ]
do
  echo "Attempting to start VMs. Attempts: $retries"
  timeout 10m time vagrant up "$@" && break
  retries=$[$retries+1]
  sleep 5
done

sleep 10