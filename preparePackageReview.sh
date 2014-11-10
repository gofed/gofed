#!/bin/sh

# $1 spec file
# $2 user
spec_file=$1
user=$2
if [ -z "$user" ]; then
	user="jchaloup"
fi;

# check if the current folder contains *.spec file
if [ ! -e $spec_file ]; then
	echo "Spec file $spec_file does not exist."
	exit
fi

# get repo name
function getValue {
        echo $1 | sed 's/[ \t][ \t]*/ /g' | cut -d' ' -f3
}
repo=$(getValue "$(cat $spec_file | grep "%global repo")")
commit=$(getValue "$(cat $spec_file | grep "%global commit")")
summary=$(cat $spec_file | grep "^Summary" | head -1 | sed 's/[ \t][ \t]*/ /g' | cut -d' ' -f2-)
echo "Parsing $spec_file file"
echo "	Repo: $repo"
echo "	Commit: $commit"
echo "	Summary: $summary"
echo ""

# copy tarball to SOURCES directory
tarball=$repo-${commit:0:7}.tar.gz
echo "Copying tarball $tarball to ~/rpmbuild/SOURCES"
cp $tarball ~/rpmbuild/SOURCES/.
echo ""

# build spec file
echo "Building spec file using rpmbuild"
rpmbuild -ba *.spec >build.log 2>&1
if [ $? -ne 0 ]; then
	echo "	Build failed. Check build.log"
	exit
fi; 
packages=$(cat build.log | grep "Wrote: " | cut -d' ' -f2)
srpm=$(cat build.log | grep "Wrote: " | cut -d' ' -f2 | grep "src.rpm$")
for package in $packages; do
	echo "	$package"
done
echo ""


# koji
echo "Running koji scratch build on srpm"
task_id=$(koji build --scratch rawhide $srpm --nowait | grep "Created task: " | cut -d' ' -f3)
echo "	Watching rawhide build, http://koji.fedoraproject.org/koji/taskinfo?taskID=$task_id"
koji watch-task $task_id --quiet
state=$(koji taskinfo $task_id | grep "State" | tr '[:upper]' '[:lower]' )
echo "	$state"

if [ "$(echo $state | cut -d' ' -f2)" != "closed" ]; then
	echo "	koji scratch build failed"
	exit
fi

# parse data for review request for bugzilla
desc_pos=$(rpm -qpi $srpm | grep -n "^Description" |  cut -d':' -f1)
wcl=$(rpm -qpi $srpm | wc -l)
rest=$(echo "$wcl-$desc_pos" | bc -l)
name=$(rpm -qpi $srpm | grep "^Name" | cut -d':' -f2 | sed 's/ *//g')

# upload the srpm to my fedora account
echo "Uploading srpm and spec file to @fedorapeople.org"
ssh $user@fedorapeople.org "mkdir -p public_html/reviews/$name" 2>/dev/null
scp $srpm $user@fedorapeople.org:public_html/reviews/$name/. 2>/dev/null
scp $spec_file $user@fedorapeople.org:public_html/reviews/$name/. 2>/dev/null
echo ""
echo ""
# generate summary and header information
echo "Generating Review Request"
echo "###############################################################"
echo "Review Request: $name - $summary"
echo "###############################################################"
echo "Spec URL: https://$user.fedorapeople.org/reviews/$name/$(basename $spec_file)"
echo ""
echo "SRPM URL: https://$user.fedorapeople.org/reviews/$name/$(basename $srpm)"
echo ""
echo "Description: $(rpm -qpi $srpm | tail -n $rest)"
echo ""
echo "Fedora Account System Username: $user"
echo ""
echo "Koji: http://koji.fedoraproject.org/koji/taskinfo?taskID=$task_id"
echo ""
echo "\$ rpmlint $(echo $(for package in $packages; do basename $package; done)) $(ls | grep *.spec)"
rpmlint $packages $(ls | grep *.spec)
echo "###############################################################"
echo ""
echo ""
echo "Enter values at: https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&format=fedora-review"
