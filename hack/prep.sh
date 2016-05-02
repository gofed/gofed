#!/bin/sh

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# pull submodules
${CUR_DIR}/pull-submodules.sh

# set PYTHONPATH
export PYTHONPATH=${CUR_DIR}/../third_party:${CUR_DIR}/../..

pushd ${CUR_DIR} >/dev/null
# render service files
echo "Rendering templates"
python render-templates.py

# symlink infra to point to gofed_infra
pushd ../third_party >/dev/null
if [ ! -e infra ]; then
	echo "Symlink infra to gofed_infra"
	ln -s gofed_infra infra
fi
popd >/dev/null

# create directory for resources and storages
pushd ${CUR_DIR}/../working_directory >/dev/null
echo "Making 'resource_client, simplefilestorage, resource_provider, storage' directories under working_directory"
mkdir -p resource_client simplefilestorage resource_provider storage
popd >/dev/null

popd >/dev/null
