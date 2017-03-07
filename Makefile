# Makefile for constructing RPMs.
# Try "make" (for SRPMS) or "make rpm"

NAME = ceph-ansible

# Set the RPM package NVR from "git describe".
# Examples:
#
#  A "git describe" value of "v2.2.0rc1" would create an NVR
#  "ceph-ansible-2.2.0-0.rc1.1.el7"
#
#  A "git describe" value of "v2.2.0rc1-1-gc465f85" would create an NVR
#  "ceph-ansible-2.2.0-0.rc1.1.gc465f85.el7"
#
#  A "git describe" value of "v2.2.0" creates an NVR
#  "ceph-ansible-2.2.0-1.el7"

VERSION := $(shell git describe --tags --abbrev=0 --match 'v*' | sed 's/^v//')
COMMIT := $(shell git rev-parse HEAD)
SHORTCOMMIT := $(shell echo $(COMMIT) | cut -c1-7)
RELEASE := $(shell git describe --tags --match 'v*' \
             | sed 's/^v//' \
             | sed 's/^[^-]*-//' \
             | sed 's/-/./')
ifeq ($(VERSION),$(RELEASE))
  RELEASE = 1
endif
ifneq (,$(findstring rc,$(VERSION)))
    RC := $(shell echo $(VERSION) | sed 's/.*rc/rc/')
    RELEASE := 0.$(RC).$(RELEASE)
    VERSION := $(subst $(RC),,$(VERSION))
endif
NVR := $(NAME)-$(VERSION)-$(RELEASE).el7

all: srpm

# Testing only
echo:
	echo COMMIT $(COMMIT)
	echo VERSION $(VERSION)
	echo RELEASE $(RELEASE)
	echo NVR $(NVR)

clean:
	rm -rf dist/
	rm -rf ceph-ansible-$(VERSION)-$(SHORTCOMMIT).tar.gz
	rm -rf $(NVR).src.rpm

dist:
	git archive --format=tar.gz --prefix=ceph-ansible-$(VERSION)/ HEAD > ceph-ansible-$(VERSION)-$(SHORTCOMMIT).tar.gz

spec:
	sed ceph-ansible.spec.in \
	  -e 's/@COMMIT@/$(COMMIT)/' \
	  -e 's/@VERSION@/$(VERSION)/' \
	  -e 's/@RELEASE@/$(RELEASE)/' \
	  > ceph-ansible.spec

srpm: dist spec
	fedpkg --dist epel7 srpm

rpm: dist srpm
	mock -r epel-7-x86_64 rebuild $(NVR).src.rpm \
	  --resultdir=. \
	  --define "dist .el7"

.PHONY: dist rpm srpm
