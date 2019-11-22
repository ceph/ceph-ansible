#!/bin/bash


vagrant box remove guits/ubuntu-bionic64 --provider libvirt || true
vagrant box remove fedora/29-atomic-host --provider libvirt || true
vagrant box remove rhel8-x86_64 --provider libvirt || true
vagrant box remove ceph/ubuntu-xenial --provider libvirt || true

retries=0
until [ $retries -ge 5 ]
do
  echo "Attempting to start VMs. Attempts: $retries"
  timeout 10m time vagrant up "$@" && break
  retries=$[$retries+1]
  sleep 5
done

sleep 10
