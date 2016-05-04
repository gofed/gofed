#!/bin/sh

# Run scan, report missing go packages and store the data under gofed/data
#
# - clone gofed/data and symlink working_directory/simplefilestorage to gofed/data/artefacts
# - gofed scan-distro -v (just for rawhide atm)
# - gofed scan-deps to report missing go packages (later push the repo to data)
# - push artefacts

# TODO(jchaloup):
# - scan-deps: add option to generate report for missing go packages
# - add options to write the report to file and stdout
# - provide gofed-bot with exclusive access to data

# Prerequisites
# - Jenkins clones all repos
# - script is customized for Jenkins Job

# we are in Jenkins's working directory
# available directories: gofed, data

pushd gofed
# setup gofed
sudo dnf install -y PyYAML python-jsonschema python2-hglib python-PyGithub python-jinja2 python-requests GitPython
sudo dnf install -y graphviz koji rpm-build
./hack/prep.sh
alias gofed=$(realpath ./hack/gofed.sh)

# symlink simplefilestorage to gofed/data
cd working_directory
rm -rf simplefilestorage
mkdir -p $WORKSPACE/data/artefacts
ln -s $WORKSPACE/data/artefacts simplefilestorage
popd

# scan distro
gofed scan-distro -v

# commit artefacts
pushd data
git add .
git commit -m "Artefacts updated: $(date)"
# no files added/updated => git commit returns non-zero

popd

# let the Jenkins clean the environment
