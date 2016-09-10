#!/bin/sh

# 1. download all snapshots (json file with unique location) from storage into working directory
#    For PoC, the json gets downloaded directly from the storage.
#    Later, it gets read via REST API

# 1. run gofed scan-distro --skip-errors: based on the latest snapshot and the current snapshot, only outdated rpms get scanned

# 1. working directory is now full with new rpms

# 1. upload generated json of new rpms into storage
#    For PoC, all the jsons gets uploaded directly to the storage
#    Later, it gets writen via REST API

# Setup working directory
echo "Setting up working directory..."
host_workdir=$(mktemp -d)
gofed_workdir="/home/gofed/gofed/working_directory/simplefilestorage"

# Prepare host workspace
pushd ${host_workdir}
echo -e "\nCloning http://github.com/gofed/data"
git clone ssh://git@github.com/gofed/data
if [ "$?" -ne 0 ]; then
	exit 1
fi

# 1. run the gofed scan-distro
echo -e "\nRunning distro scan"
docker run -u gofed -v ${host_workdir}/data:${gofed_workdir} -t gofed/gofed:v1.0.0 /home/gofed/gofed/hack/gofed.sh scan-distro -s --target="Fedora:rawhide" --verbose

# 1. upload generated json of new rpms into storage
echo -e "\nCommiting changes"
cd data
git add . && git commit -m "Distro scan from $(date)" && git push

popd
rm -rf ${host_workdir}
