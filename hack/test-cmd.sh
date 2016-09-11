#!/bin/bash -x

set -eu
set -o pipefail

#$ gofed 
#Synopsis: gofed command [arg1 [arg2 ...]]
#
#	apidiff           compare API of two commits of the same golang project
#	bbo               buildroot override builds for all branches
#	bitbucket2spec    generate spec file from bitbucket
#	build             build all fedora branches
#	bump              bump spec file
#	check-deps        check packages for commit
#	client            gofed-web service quering
#	fetch             fetch resource for target, e.g. download tarball for spec file
#	gcpmaster         git cherry pick master branch
#	ggi               get golang imports
#	github2spec       generate spec file from github
#	googlecode2spec   generate spec file from googlecode
#	help              print help
#	inspect           inspect golang tarball
#	lint              lint for golang spec files
#	pull              pull from branches
#	push              push to branches
#	repo2spec         generate spec file from repository import path
#	review            creates review for Bugzilla
#	scan-deps         scan all golang packages for dependencies (e.g. cyclic)
#	scan-distro       scan distribution
#	scan-packages     scan packages
#	scratch-build     scratch build all fedora branches
#	ticket            Create tracker for a golang package or find one if already created
#	tools             tools for packaging
#	update            update all fedora branches
#	version           print gofed version
#	wizard            run phases of bulding, updating, ... at once

###########################
### Test basic commands ###
###########################

gofed_binary="./gofed"
flags="--dry-run -v"

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# set PYTHONPATH
export PYTHONPATH=${CUR_DIR}/../third_party:${CUR_DIR}/../third_party/cmdsignature:${CUR_DIR}/../..
export GOFED_DEVEL=1

### bbo ###
${gofed_binary} bbo ${flags} fake-build-name

### build ###
${gofed_binary} build ${flags}

### check-deps ###
${gofed_binary} check-deps --godeps=${CUR_DIR}/testdata/Godeps.json ${flags}

### pull ###
${gofed_binary} pull ${flags}

### push ###
${gofed_binary} push ${flags}

### scan-deps ###
${gofed_binary} scan-deps -g ${flags}

### scan-distro ###
${gofed_binary} scan-distro --target="Fedora:rawhide" ${flags}

### scan-packages ###
${gofed_binary} scan-packages --atmost 10000 ${flags}

### scratch-build ###
${gofed_binary} scratch-build ${flags}

### tools ###
for flag in --merge-master --git-reset --pull --push --scratch --build --update; do
	${gofed_binary} tools ${flags} $flag
done

${gofed_binary} tools ${flags} --bbo fake-build-name

${gofed_binary} tools ${flags} --wait fake-build-name

${gofed_binary} tools ${flags} --waitbbo fake-build-name

### update ###
${gofed_binary} update ${flags}

### version ###
${gofed_binary} version

### wizard ###
${gofed_binary} wizard --scratch ${flags}
