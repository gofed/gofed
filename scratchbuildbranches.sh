#!/bin/sh

# ####################################################################
# go2fed - set of tools to automize packaging of golang devel codes
# Copyright (C) 2014  Jan Chaloupka, jchaloup@redhat.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# ####################################################################

BUILDSFILE="builds.taskid"
script_dir=$(dirname $0)

# TODO
# [  ] - help
# [  ] - options (just wait, raw builds, scratch-builds implicit)
# [  ] - dry run (just print commands)
# [  ] - rewrite into python?

function processBranch {
	fedpkg switch-branch $1
	task_id=-1
	if [ "$3" == "scratch-build" ]; then
		srpm=$(fedpkg srpm | grep Wrote | cut -d' ' -f2)
		echo "Srpm $srpm created"
		task_id=$(fedpkg scratch-build --nowait --srpm=$srpm | grep "Created task: " | cut -d' ' -f3)
	else
		task_id=$(fedpkg build --nowait | grep "Created task: " | cut -d' ' -f3)
	fi

	echo "$1:$task_id" >> $2
	if [ "$3" == "scratch-build" ]; then
		echo "Scratch build http://koji.fedoraproject.org/koji/taskinfo?taskID=$task_id initiated"
	else
		echo "Raw build http://koji.fedoraproject.org/koji/taskinfo?taskID=$task_id initiated"
	fi
}

# wait for all scratch builds to end
function waitForBuild {
	for task in $(cat $1); do
		branch=$(echo $task | cut -d':' -f1)
		task_id=$(echo $task | cut -d':' -f2)
		echo "Watching $branch branch, http://koji.fedoraproject.org/koji/taskinfo?taskID=$task_id"
		koji watch-task $task_id --quiet
	done
}

# check state of all builds
function checkBuilds {
	ok=1
	for task in $(cat $1); do
		branch=$(echo $task | cut -d':' -f1)
		taskid=$(echo $task | cut -d':' -f2)
		state=$(koji taskinfo $taskid | grep  State | cut -d' ' -f2)
		echo "$branch: $state"
		if [ "$state" != "closed" ]; then
			ok=0
		fi
	done
	if [ "$ok" -eq 1 ]; then
		exit 0
	else
		exit 1
	fi
}

# options
build="scratch-build"
if [ "$1" == "raw" ]; then
	build="build"
fi

# get branches
branches=$(cat $script_dir/config/go2fed.conf | grep "^branches:" | cut -d':' -f2)
if [ "$branches" == "" ]; then
	branches=$(git branch --list | sed 's/\*//g' | grep -v "el6")
fi

rm -f $BUILDSFILE
for branch in $branches; do
	processBranch $branch $BUILDSFILE $build
done

echo ""
echo "Waiting for builds..."
waitForBuild $BUILDSFILE
echo ""
echo "Checking finished builds..."
checkBuilds $BUILDSFILE
