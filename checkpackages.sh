#!/bin/sh
echo "upstream                                 fedora                                   status     repo"
for repo in $(cat golang.list); do
	./checkpackage.py $repo
done
