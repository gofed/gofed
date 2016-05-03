#!/bin/sh

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "removing rendered services"
rm -f ${CUR_DIR}/daemons/*.service

echo "removing infra->gofed_infra symlink"
rm -f ${CUR_DIR}/../third_party/infra

echo "removing directories under working_directory"
pushd ${CUR_DIR}/../working_directory/ >/dev/null
rm -rf resource_client simplefilestorage resource_provider storage
popd >/dev/null

echo "git checkout replaced infra.conf and resources.conf files"
pushd ${CUR_DIR}/../third_party/gofed_infra >/dev/null
git checkout system/config/infra.conf
cd ../gofed_resources
git checkout config/resources.conf
popd >/dev/null
