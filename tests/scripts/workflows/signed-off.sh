#!/bin/bash
set -x

if [[ "$(git log --oneline --no-merges origin/"${GITHUB_BASE_REF}"..HEAD | wc -l)" -ne "$(git log --no-merges origin/"${GITHUB_BASE_REF}"..HEAD | grep -c Signed-off-by)" ]]; then
  echo "One or more commits is/are missing a Signed-off-by. Add it with 'git commit -s'."
  exit 1
else
  echo "Sign-off ok!"
fi