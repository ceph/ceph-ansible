#!/bin/bash


OUTPUT="$(uname -s)"
case "${OUTPUT}" in
    Linux*)     CLI=sha1sum;;
    Darwin*)    CLI=shasum;;
    *)          echo "Unknown system"; exit 1
esac

find ./tests -maxdepth 1 -type l -delete
pushd tests
for dir in $(find ./functional/{centos,ubuntu} -mindepth 2 -maxdepth 2 -type d)
do
  ln -sf ${dir} $(echo "${dir}" | "${CLI}" | cut -c -7)
done
popd
