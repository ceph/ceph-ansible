#!/bin/bash -e
#
# Copyright (C) 2014, 2015 Red Hat <contact@redhat.com>
#
# Author: Daniel Lin <danielin@umich.edu>
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#

if test -f /etc/redhat-release ; then
  PACKAGE_INSTALLER=yum
elif type apt-get > /dev/null 2>&1 ; then
  PACKAGE_INSTALLER=apt-get
else
  echo "ERROR: Package Installer could not be determined"
  exit 1
fi

while read p; do
  if [[ $p =~ ^#.* ]] ; then
    continue
  fi
  $PACKAGE_INSTALLER install $p -y
done < $1
