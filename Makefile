# Makefile for constructing RPMs.
# Try "make" (for SRPMS) or "make rpm"

NAME = ceph-ansible

# Set the RPM package NVR from "git describe".
# Examples:
#
#  A "git describe" value of "v2.2.0beta1" would create an NVR
#  "ceph-ansible-2.2.0-0.beta1.1.el7"
#
#  A "git describe" value of "v2.2.0rc1" would create an NVR
#  "ceph-ansible-2.2.0-0.rc1.1.el7"
#
#  A "git describe" value of "v2.2.0rc1-1-gc465f85" would create an NVR
#  "ceph-ansible-2.2.0-0.rc1.1.gc465f85.el7"
#
#  A "git describe" value of "v2.2.0" creates an NVR
#  "ceph-ansible-2.2.0-1.el7"

TAG := $(shell git describe --tags --abbrev=0 --match 'v*')
VERSION := $(shell echo $(TAG) | sed 's/^v//')
COMMIT := $(shell git rev-parse HEAD)
SHORTCOMMIT := $(shell echo $(COMMIT) | cut -c1-7)
RELEASE := $(shell git describe --tags --match 'v*' \
             | sed 's/^v//' \
             | sed 's/^[^-]*-//' \
             | sed 's/-/./')
ifeq ($(VERSION),$(RELEASE))
  RELEASE = 1
endif
ifneq (,$(findstring beta,$(VERSION)))
    BETA := $(shell echo $(VERSION) | sed 's/.*beta/beta/')
    RELEASE := 0.$(BETA).$(RELEASE)
    VERSION := $(subst $(BETA),,$(VERSION))
endif
ifneq (,$(findstring rc,$(VERSION)))
    RC := $(shell echo $(VERSION) | sed 's/.*rc/rc/')
    RELEASE := 0.$(RC).$(RELEASE)
    VERSION := $(subst $(RC),,$(VERSION))
endif

ifneq (,$(shell echo $(VERSION) | grep [a-zA-Z]))
    # If we still have alpha characters in our Git tag string, we don't know
    # how to translate that into a sane RPM version/release. Bail out.
    $(error cannot translate Git tag version $(VERSION) to an RPM NVR)
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
	rpmbuild -bs ceph-ansible.spec \
	  --define "_topdir ." \
	  --define "_sourcedir ." \
	  --define "_srcrpmdir ." \
	  --define "dist .el7"

rpm: dist srpm
	mock -r epel-7-x86_64 rebuild $(NVR).src.rpm \
	  --resultdir=. \
	  --define "dist .el7"

tag:
	$(eval BRANCH := $(shell git rev-parse --abbrev-ref HEAD))
	$(eval LASTNUM := $(shell echo $(TAG) \
	                    | sed -E "s/.*[^0-9]([0-9]+)$$/\1/"))
	$(eval NEXTNUM=$(shell echo $$(($(LASTNUM)+1))))
	$(eval NEXTTAG=$(shell echo $(TAG) | sed "s/$(LASTNUM)$$/$(NEXTNUM)/"))
	if [[ "$(TAG)" == "$(git describe --tags --match 'v*')" ]]; then \
	    echo "$(SHORTCOMMIT) on $(BRANCH) is already tagged as $(TAG)"; \
	    exit 1; \
	fi
	if [[ "$(BRANCH)" != "master" ]] && \
	   ! [[ "$(BRANCH)" =~ ^stable- ]]; then \
		echo Cannot tag $(BRANCH); \
		exit 1; \
	fi
	@echo Tagging Git branch $(BRANCH)
	git tag $(NEXTTAG)
	@echo run \'git push origin $(NEXTTAG)\' to push to GitHub.

.PHONY: dist rpm srpm tag
