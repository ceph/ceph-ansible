# Makefile for constructing RPMs.
# Try "make" (for SRPMS) or "make rpm"

NAME = ceph-ansible
VERSION := $(shell git describe --tags --abbrev=0)
COMMIT := $(shell git rev-parse HEAD)
SHORTCOMMIT := $(shell echo $(COMMIT) | cut -c1-7)
RELEASE := $(shell git describe --tags --match 'v*' \
             | sed 's/^v//' \
             | sed 's/^[^-]*-//' \
             | sed 's/-/./')
ifeq ($(VERSION),$(RELEASE))
  RELEASE = 0
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
