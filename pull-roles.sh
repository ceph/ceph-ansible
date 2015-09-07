#!/bin/bash

owner="leseb"
roles="ceph-common ceph-mds ceph-mon ceph-osd ceph-restapi ceph-rgw"
role_dir="$PWD/roles"

[ ! -d $role_dir ] && mkdir $role_dir

if [[ -n "$(find $role_dir -prune -empty)" ]]; then
  for r in $roles
  do
    ansible-galaxy install -f $owner.$r -p $role_dir
  done
fi

for i in $(ls roles)
do
    mv ./roles/${i} ./roles/${i#leseb.}
done
