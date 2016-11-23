#!/bin/bash
set -xe

# VARIABLES
BASEDIR=$(dirname "$0")
LOCAL_BRANCH=$(cd $BASEDIR && git rev-parse --abbrev-ref HEAD)
BRANCHES="master ansible-1.9"
ROLES="ceph-common ceph-mon ceph-osd ceph-mds ceph-rgw ceph-restapi ceph-agent ceph-fetch-keys ceph-rbd-mirror ceph-client"


# FUNCTIONS
function check_existing_remote {
  if ! git remote show $1 &> /dev/null; then
    git remote add $1 git@github.com:/ceph/ansible-$1.git
  fi
}

function pull_origin {
  git pull origin --tags
}

function reset_hard_origin {
  # let's bring everything back to normal
  git checkout $LOCAL_BRANCH
  git fetch origin
  git fetch --tags
  git reset --hard origin/master
}

function check_git_status {
  if [[ $(git status --porcelain | wc -l) -gt 0 ]]; then
    echo "It looks like the following changes haven't been committed yet"
    echo ""
    git status --short
    echo ""
    echo ""
    echo "Do you really want to continue?"
    echo "Press ENTER to continue or CTRL C to break"
    read
  fi
}


# MAIN
check_git_status
trap reset_hard_origin EXIT
trap reset_hard_origin ERR
pull_origin

for ROLE in $ROLES; do
  # For readability we use 2 variables with the same content
  # so we always make sure we 'push' to a remote and 'filter' a role
  REMOTE=$ROLE
  check_existing_remote $REMOTE
  reset_hard_origin
  # First we filter branches by rewriting master with the content of roles/$ROLE
  # this gives us a new commit history
  for BRANCH in $BRANCHES; do
    git checkout -B $BRANCH origin/$BRANCH
    git filter-branch -f --prune-empty --subdirectory-filter roles/$ROLE
    git push $REMOTE $BRANCH
  done
  reset_hard_origin
  # then we filter tags starting from version 2.0 and push them
  for TAG in $(git tag | egrep '^v[2-9].[0-9]*.[0-9]*$'); do
    git filter-branch -f --prune-empty --subdirectory-filter roles/$ROLE $TAG
    git push $REMOTE $TAG
    reset_hard_origin
  done
done
