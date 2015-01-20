#!/bin/sh

script_dir=$(dirname $0)

function processBranch {
        fedpkg switch-branch $1
	#bodhi --new --type newpackage --notes 'First package for Fedora' golang-github-vaughan0-go-ini-0-0.2.gita98ad7e.el6
        fedpkg update
}


# get branches
branches=$(cat $script_dir/config/go2fed.conf | grep "^branches:" | cut -d':' -f2)
if [ "$branches" == "" ]; then
        branches=$(git branch --list | sed 's/\*//g' | grep -v "el6")
fi

for branch in $(echo $branches | sed 's/master//g'); do
        processBranch $branch
done

