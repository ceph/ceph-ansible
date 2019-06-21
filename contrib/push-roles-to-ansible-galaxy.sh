#!/bin/bash
set -xe

# VARIABLES
BASEDIR=$(dirname "$0")
LOCAL_BRANCH=$(cd $BASEDIR && git rev-parse --abbrev-ref HEAD)
ROLES="ceph-common ceph-mon ceph-osd ceph-mds ceph-rgw ceph-fetch-keys ceph-rbd-mirror ceph-client ceph-container-common ceph-mgr ceph-defaults ceph-config"


# FUNCTIONS
function goto_basedir {
  TOP_LEVEL=$(cd $BASEDIR && git rev-parse --show-toplevel)
  if [[ "$(pwd)" != "$TOP_LEVEL" ]]; then
    pushd "$TOP_LEVEL"
  fi
}

function check_existing_remote {
  if ! git remote show "$1" &> /dev/null; then
    git remote add "$1" git@github.com:/ceph/ansible-"$1".git
  fi
}

function pull_origin {
  git pull origin master
}

function reset_hard_origin {
  # let's bring everything back to normal
  git checkout "$LOCAL_BRANCH"
  git fetch origin --prune
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
    read -r
  fi
}

function compare_tags {
  # compare local tags (from https://github.com/ceph/ceph-ansible/) with distant tags (from https://github.com/ceph/ansible-ceph-$ROLE)
  local tag_local
  local tag_remote
  for tag_local in $(git tag | grep -oE '^v[2-9].[0-9]*.[0-9]*$' | sort -t. -k 1,1n -k 2,2n -k 3,3n -k 4,4n); do
    tags_array+=("$tag_local")
  done
  for tag_remote in $(git ls-remote --tags "$1" | grep -oE 'v[2-9].[0-9]*.[0-9]*$' | sort -t. -k 1,1n -k 2,2n -k 3,3n -k 4,4n); do
    remote_tags_array+=("$tag_remote")
  done

  for i in "${tags_array[@]}"; do
    skip=
    for j in "${remote_tags_array[@]}"; do
      [[ "$i" == "$j" ]] && { skip=1; break; }
    done
    [[ -n $skip ]] || tag_to_apply+=("$i")
  done
}

# MAIN
goto_basedir
check_git_status
trap reset_hard_origin EXIT
trap reset_hard_origin ERR
pull_origin

for ROLE in $ROLES; do
  # For readability we use 2 variables with the same content
  # so we always make sure we 'push' to a remote and 'filter' a role
  REMOTE=$ROLE
  check_existing_remote "$REMOTE"
  reset_hard_origin
  # First we filter branches by rewriting master with the content of roles/$ROLE
  # this gives us a new commit history
  for BRANCH in $(git branch --list --remotes "origin/stable-*" "origin/master" "origin/ansible-1.9" | cut -d '/' -f2); do
    git checkout -B "$BRANCH" origin/"$BRANCH"
    # use || true to avoid exiting in case of 'Found nothing to rewrite'
    git filter-branch -f --prune-empty --subdirectory-filter roles/"$ROLE" || true
    git push -f "$REMOTE" "$BRANCH"
  done
  reset_hard_origin
  # then we filter tags starting from version 2.0 and push them
  compare_tags "$ROLE"
  if [[ ${#tag_to_apply[@]} == 0 ]]; then
    echo "No new tag to push."
    continue
  fi
  for TAG in "${tag_to_apply[@]}"; do
    # use || true to avoid exiting in case of 'Found nothing to rewrite'
    git filter-branch -f --prune-empty --subdirectory-filter roles/"$ROLE" "$TAG" || true
    git push -f "$REMOTE" "$TAG"
    reset_hard_origin
  done
done
trap - EXIT ERR
popd &> /dev/null
