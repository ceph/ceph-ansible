#!/bin/bash

set -ex

function git_diff_to_head {
  git diff --diff-filter=MT --no-color origin/"${GITHUB_BASE_REF}"..HEAD
}

function match_file {
  git_diff_to_head | sed -n "s|^+++.*\\($1.*\\)|\\1|p"
}

# group_vars / defaults
match_file "/defaults/main.yml"
nb=$(match_file "/defaults/main.yml" | wc -l)
if [[ "$nb" -eq 0 ]]; then
  echo "group_vars has not been touched."
else
  match_file "group_vars/"
  nb_group_vars=$(match_file "group_vars/" | wc -l)
  if [[ "$nb" -gt "$nb_group_vars" ]]; then
    echo "One or more files containing default variables has/have been modified."
    echo "You must run 'generate_group_vars_sample.sh' to generate the group_vars template files."
    exit 1
  fi
fi

# ceph_release_num[ceph_release] statements check
if match_file "roles/ceph-defaults/" | grep -E '^[<>+].*- ceph_release_num\[ceph_release\]'; then
  echo "Do not use statements like '- ceph_release_num[ceph_release]' in ceph-defaults role!"
  echo "'ceph_release' is only populated **after** the play of ceph-defaults, typically in ceph-common or ceph-docker-common."
  exit 1
fi
echo "No '- ceph_release_num[ceph_release]' statements found in ceph-defaults role!"
