#!/bin/sh

# $1 pkg_name
# $2 review request bug id

script_dir=$(dirname $0)

if [ "$1" == "" ]; then
	echo "Missing package name"
	exit 1
fi

if [ "$2" == "" ]; then
	echo "Missing review request bug ID"
	exit 1
fi

pkg_name=$1
bug_id=$2


############# clone the repo and cd to its directory #############
# $1 ... pkg_name
function dirExists {
	ls $1/fedora/$1 >/dev/null 2>/dev/null
	echo $?
}

# $1 ... pkg_name
function cloneRepo {
	mkdir -p $1
	cd $1
	mkdir -p fedora
	cd fedora
	fedpkg clone $1
}


############# download srpm #############
# $1 ... pkg_name
function downloadSrpm {
	srpm=$(ssh jchaloup@fedorapeople.org "ls public_html/reviews/$1/*.src.rpm")
	srpm=$(basename $srpm)
	wget -q https://jchaloup.fedorapeople.org/reviews/$1/$srpm >/dev/null 2>/dev/null
	if [ "$?" -eq 0 ]; then
		echo $srpm
	else
		echo ""
	fi
}

############# import srpm to repo #############
# $1 ... srpm
function importSrpm {
	fedpkg import $1
}

############# has resolves: #bug_id? #############
# $1 ... pkg_name
# $2 ... bug_id
function hasResolves {
	has_resolves=$(cat *.spec | grep resolves | grep $2 | wc -l)
	if [ "$has_resolves" -eq 0 ]; then
		echo "Missing Resolves: #$2"
		read -p "Open vim? [y/n]. n means quit: " input
		if [ "$input" == "y" ]; then
			echo "  resolves: #$2" >> ${1}.spec
			vi *.spec
			read -p "Continue? [y/n]: " input
			if [ "$input" == "n" ]; then
				exit 1
			fi
		else
			exit 1
		fi
		git add *.spec
		git commit --verbose
	fi
}

############# clone master to all other branches #############
function cloneMasterToBranches {
	branches=$(cat $script_dir/config/go2fed.conf | grep "^branches:" | cut -d':' -f2 | sed 's/master//')
	if [ "$branches" == "" ]; then
	        branches=$(git branch --list | sed 's/\*//g' | grep -v "el6")
	fi

	for branch in $branches; do
		fedpkg switch-branch $branch
	        git reset --hard master
	done
}

############# scratch build of all branches #############
function scratchBuildBranches {
	go2fed scratch-build
	ret=$?
	echo "Return value: $ret"
	read -p "Continue? [y/n]: " input
	if [ "$input" == "n" ]; then
		exit 1
	fi
}

############# push and build of all branches #############
function pushAndBuildBranches {
	go2fed parallel-push
	go2fed build
	ret=$?
	echo "Return value: $ret"
	read -p "Continue? [y/n]: " input
	if [ "$input" == "n" ]; then
		exit 1
	fi
}

############# update all branches except master and f22 #############
function updateBranches {
	go2fed update
}

# $1 ... pkg_name
function bboBuilds {
	srpm=$(ssh jchaloup@fedorapeople.org "ls public_html/reviews/$1/*.src.rpm")
	srpm=$(basename $srpm)
	build=$(echo $srpm | rev | sed 's/^[^.]*\.[^.]*\.[^.]*\.//' | rev)
	read -p "$build detected. Continue? [y/n]: " input
	if [ "$input" == "n" ]; then
		exit 1
	fi
	go2fed bbo $build
}

state_file=".initpkg.state"
#echo "#### cache of go2fed initpkg ####" > $state_file

e=$(dirExists $pkg_name)
if [ "$e" -eq 0 ]; then
	cd $pkg_name/fedora/$pkg_name
	if [ ! -f $state_file ]; then
		echo "# clone the repo and cd to its directory" >> $state_file
	        echo "1: $(pwd)" >> $state_file
	fi
else
	cloneRepo $pkg_name
	cd $pkg_name/fedora/$pkg_name
	echo "# clone the repo and cd to its directory" >> $state_file
	echo "1: $(pwd)" >> $state_file
fi

# get the last step executed
# this loop handles empty lines
for line in $(cat $state_file | grep -v "^#" | cut -d':' -f1); do
	last_step=$line
done

STEP_CLONE_REPO=1
STEP_DOWNLOAD_SRPM=2
STEP_IMPORT_SRPM=3
STEP_HAS_RESOLVES=4
STEP_CLONE_TO_BRANCHES=5
STEP_SCRATCH_BUILD=6
STEP_PUSH_AND_BUILD=7
STEP_UPDATE_BRANCHES=8
STEP_OVERRIDE=9

if [ "$last_step" -lt $STEP_DOWNLOAD_SRPM ]; then
	srpm=$(downloadSrpm $pkg_name)
	if [ "$srpm" == "" ]; then
		echo "Unable to wget SRPM"
		exit 1
	fi
	echo "# download srpm" >> $state_file
	echo "2: $srpm" >> $state_file
else
	echo "skipping:" $(cat $state_file | grep -v "^#" | grep "^$STEP_DOWNLOAD_SRPM:")
fi

if [ "$last_step" -lt $STEP_IMPORT_SRPM ]; then
	importSrpm $pkg_name
	echo "# import srpm" >> $state_file
	echo "3: srpm imported" >> $state_file
else
	echo "skipping:" $(cat $state_file | grep -v "^#" | grep "^$STEP_IMPORT_SRPM:")
fi

if [ "$last_step" -lt $STEP_HAS_RESOLVES ]; then
	hasResolves $pkg_name $bug_id
	echo "# has resolves" >> $state_file
	echo "4: resolves: #$bug_id " >> $state_file
else
	echo "skipping:" $(cat $state_file | grep -v "^#" | grep "^$STEP_HAS_RESOLVES:")
fi

if [ "$last_step" -lt $STEP_CLONE_TO_BRANCHES ]; then
	cloneMasterToBranches
	echo "# clone master to other branches" >> $state_file
	echo "5: cloned to other branches " >> $state_file
else
	echo "skipping:" $(cat $state_file | grep -v "^#" | grep "^$STEP_CLONE_TO_BRANCHES:")
fi

if [ "$last_step" -lt $STEP_SCRATCH_BUILD ]; then
	scratchBuildBranches
	echo "# scratch build branches" >> $state_file
	echo "6: scratch build branches " >> $state_file
else
	echo "skipping:" $(cat $state_file | grep -v "^#" | grep "^$STEP_SCRATCH_BUILD:")
fi

if [ "$last_step" -lt $STEP_PUSH_AND_BUILD ]; then
	pushAndBuildBranches
	echo "# build branches" >> $state_file
	echo "7: build branches " >> $state_file
else
	echo "skipping:" $(cat $state_file | grep -v "^#" | grep "^$STEP_PUSH_AND_BUILD:")
fi

if [ "$last_step" -lt $STEP_UPDATE_BRANCHES ]; then
	updateBranches
	echo "# update branches" >> $state_file
	echo "8: update branches " >> $state_file
else
	echo "skipping:"  $(cat $state_file | grep -v "^#" | grep "^$STEP_UPDATE_BRANCHES:")
fi

if [ "$last_step" -lt $STEP_OVERRIDE ]; then
	bboBuilds $pkg_name
	echo "# buildroot override branches" >> $state_file
	echo "9: buildroot override branches " >> $state_file
else
	echo "skipping:"  $(cat $state_file | grep -v "^#" | grep "^$STEP_OVERRIDE:")
fi
