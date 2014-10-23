#!/bin/sh
for repo in $(cat golang.list); do
	./checkpackage.py $repo
done
