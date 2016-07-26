#!/bin/sh

# 1. download all snapshots (json file with unique location) from storage into working directory
#    For PoC, the json gets downloaded directly from the storage.
#    Later, it gets read via REST API

# 1. run gofed scan-distro --skip-errors: based on the latest snapshot and the current snapshot, only outdated rpms get scanned

# 1. working directory is now full with new rpms

# 1. upload generated json of new rpms into storage
#    For PoC, all the jsons gets uploaded directly to the storage
#    Later, it gets writen via REST API

#### Code input ####
export os="Fedora"
export distro="rawhide"

#### Code logic ####
host_workdir=$(mktemp -d)
gofed_workdir="/home/gofed/gofed/working_directory/simplefilestorage"

# Prepare host workspace
pushd ${host_workdir}
mkdir -p golang-distribution-snapshot/${os}/${distro}/

# Download all snapshots
curl -f https://jchaloup.fedorapeople.org/gofed/data/golang-distribution-snapshot/${os}/${distro}/data.json -o golang-distribution-snapshot/${os}/${distro}/data.json

# 1. run the gofed scan-distro
docker run -v ${host_workdir}:${gofed_workdir} -t gofed/gofed:v1.0.0 gofed scan-distro -s

# 1. upload generated json of new rpms into storage
