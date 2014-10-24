#!/bin/sh

function processBranch {
        fedpkg switch-branch $1
        fedpkg update
}


# get branches
for branch in $(git branch --list | sed 's/\*//g' | grep -v "el6" | grep -v "master"); do
        processBranch $branch
done

