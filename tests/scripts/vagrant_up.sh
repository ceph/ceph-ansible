#!/bin/bash

retries=0
until [ $retries -ge 5 ]
do
  echo "Attempting to start VMs. Attempts: $retries"
  timeout 10m time vagrant up "$@" && break
  retries=$[$retries+1]
  sleep 5
done

sleep 10