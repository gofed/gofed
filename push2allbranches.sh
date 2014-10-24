#!/bin/sh

function processBranch {
	fedpkg switch-branch $1
	fedpkg push
}


# get branches
for branch in $(git branch --list | sed 's/\*//g' | grep -v "el6"); do
	processBranch $branch
done

