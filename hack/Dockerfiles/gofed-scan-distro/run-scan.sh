#!/bin/sh -x

user=${1}
target=${2}

kinit ${user} -k -t /etc/username.keytab

# Setup working directory
pushd /home/gofed/gofed/working_directory
echo -e "\nCloning http://github.com/gofed/data"
git clone ssh://git@github.com/gofed/data simplefilestorage
if [ "$?" -ne 0 ]; then
        exit 1
fi

# TODO(jchaloup): read whitelist of go packages
echo -e "\nRunning distro scan"
/home/gofed/gofed/hack/gofed.sh scan-distro -s --target="${target}" --verbose
if [ "$?" -ne 0 ]; then
        exit 1
fi

# 1. upload generated json of new rpms into storage
echo -e "\nCommiting changes"
git add . && git commit -m "Distro scan from $(date)" && git push

popd
