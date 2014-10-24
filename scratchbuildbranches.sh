#!/bin/sh
BUILDSFILE="builds.taskid"

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
	for task in $(cat $1); do
		branch=$(echo $task | cut -d':' -f1)
		taskid=$(echo $task | cut -d':' -f2)
		state=$(koji taskinfo $taskid | grep  State | cut -d' ' -f2)
		echo "$branch: $state"
	done
}

# options
build="scratch-build"
if [ "$1" == "raw" ]; then
	build="build"
fi

# get branches
rm -f $BUILDSFILE
for branch in $(git branch --list | sed 's/\*//g' | grep -v "el6"); do
	processBranch $branch $BUILDSFILE $build
done

echo ""
echo "Waiting for builds..."
waitForBuild $BUILDSFILE
echo ""
echo "Checking finished builds..."
checkBuilds $BUILDSFILE
