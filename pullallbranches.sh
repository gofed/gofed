#!/bin/sh

script_dir=$(dirname $0)

function processBranch {
	fedpkg switch-branch $1
	fedpkg pull
}

# get branches
branches=$(cat $script_dir/config/go2fed.conf | grep "^branches:" | cut -d':' -f2)
if [ "$branches" == "" ]; then
        branches=$(git branch --list | sed 's/\*//g' | grep -v "el6")
fi

for branch in $branches; do
	processBranch $branch
done

