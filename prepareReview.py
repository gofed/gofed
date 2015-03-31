import os.path
import optparse
from modules.Config import Config
from modules.specParser import SpecInfo
import shutil
from os.path import expanduser
from modules.Utils import runCommand

if __name__ == "__main__":
	parser = optparse.OptionParser("%prog")

	parser.add_option(
	    "", "-u", "--user", dest="user", default = "",
	    help = "FAS username"
        )

	parser.add_option(
	    "", "", "--skip-koji", dest="skipkoji", action = "store_true", default = False,
	    help = "don't run koji build"
        )

	options, args = parser.parse_args()

	if len(args) != 1:
		print "Synopsis: [--user=USER|-u USER] [--skip-koji] SPEC"
		exit(1)
	specfile = args[0]

	user = options.user
	if user == "":
		user = Config().getFASUsername()

	if not os.path.exists(specfile):
		print "Spec file %s not found" % specfile
		exit(1)

	obj = SpecInfo(specfile)

	provider = obj.getMacro("provider")
	repo = obj.getMacro("repo")
	commit = obj.getMacro("commit")
	summary = obj.getTag("summary")
	name = obj.getTag("name")

	print "Parsing %s file" % specfile
	print "  Provides: %s" % provider
	print "  Repo: %s" % repo
	print "  Commit: %s" % commit
	print "  Name: %s" % name
	print "  Summary: %s" % summary
	print ""

	if provider == "":
		print "Provider macro is missing"
		exit(1)
	if repo == "":
		print "Repo macro is missing"
		exit(1)
	if commit == "":
		print "Commit macro is missing"
		exit(1)
	if name == "":
		print "Name tag is missing"
		exit(1)
	if summary == "":
		print "Summary tag is missing"
		exit(1)

	if provider == "bitbucket":
		tarball = "%s.zip" % commit[:12]
	else:
		tarball = "%s-%s.tar.gz" % (repo, commit[:7])

	# copy tarball to ~/rpmbuild/SOURCES
	print "Copying tarball %s to %s/rpmbuild/SOURCES" % (tarball, expanduser("~"))
	try:
		shutil.copyfile(tarball, '%s/rpmbuild/SOURCES/%s' % (expanduser("~"), tarball))
	except IOError, e:
		print "Unable to copy tarball %s: %s" % (tarball, e)
		exit(1)

	print ""

	# build spec file
	print "Building spec file using rpmbuild"
	so, se, rc = runCommand("rpmbuild -ba %s" % specfile)
	if rc != 0:
		print "  Build failed. Check build.log."
		print "  Error: %s" % se
		exit(1)

	builds = filter(lambda l: l.startswith("Wrote:"), so.split("\n"))
	builds = map(lambda l: l.split(" ")[1], builds)
	srpm = filter(lambda l: l.endswith("src.rpm"), builds)[0]

	for build in builds:
		print "  %s" % build
	print ""

	# rpmlint
	print "Running rpmlint %s" % " ".join(builds)
	so, se, rc = runCommand("rpmlint %s" % " ".join(builds))
	if rc != 0:
		print "Unable to run rpmlint: %s" % se
		exit(1)

	rpmlint = so
	print so

	# build in koji
	if not options.skipkoji:
		print "Running koji scratch build on srpm"
		print "koji build --scratch rawhide %s --nowait" % srpm
		so, se, rc = runCommand("koji build --scratch rawhide %s --nowait" % srpm)
		if rc != 0:
			print "Unable to run scratch build: %s" % se
			exit(1)

		task = filter(lambda l: l.startswith("Created task: "), so.split("\n"))
		if task == []:
			print "Unable to get task id"
			exit(1)

		task_id = task[0].split("Created task: ")[1]

		print "  Watching rawhide build, http://koji.fedoraproject.org/koji/taskinfo?taskID=%s" % task_id

		_, se, rc = runCommand("koji watch-task %s --quiet" % task_id)
		if rc != 0:
			print "Unable to wait for the task: %s" % se
			exit(1)

		so, se, rc = runCommand("koji taskinfo %s" % task_id)
		if rc != 0:
			print "Unable to get task info: %s" % se
			exit(1)

		state = filter(lambda l: l.startswith("State"), so.split("\n"))
		if state == []:
			print "Unable to get task state"
			exit(1)

		state = state[0].split("State: ")[1].lower()
		if state != "closed":
			print "  koji scratch build failed"
			exit(1)

	# parse data for review request for bugzilla
	so, se, rc = runCommand("rpm -qpi %s" % srpm)
	if rc != 0:
		print "Unable to get info from srpm: %s" % se
		exit(1)

	# description is the last item
	index = 0
	lines = so.split("\n")
	for line in lines:
		if not line.startswith("Description"):
			index +=1
			continue
		break

	description = "\n".join(lines[index+1:-1])

	# upload the srpm to my fedora account
	rc = 0
	print "Uploading srpm and spec file to @fedorapeople.org"
	print '%s@fedorapeople.org "mkdir -p public_html/reviews/%s"' % (user, name)
	#so, se, rc = runCommand('ssh %s@fedorapeople.org "mkdir -p public_html/reviews/%s"' % (user, name))
	if rc != 0:
		print "Unable to create public_html/reviews/%s dir: %s" % (name, se)
		exit(1)

	print "scp %s %s@fedorapeople.org:public_html/reviews/%s/." % (srpm, user, name)
	#so, se, rc = runCommand("scp %s %s@fedorapeople.org:public_html/reviews/%s/." % (srpm, user, name))
	if rc != 0:
		print "Unable to copy srpm to fedorapeople.org: %s" % se
		exit(1)

	print "scp %s %s@fedorapeople.org:public_html/reviews/%s/." % (specfile, user, name)
	#so, se, rc = runCommand("scp %s %s@fedorapeople.org:public_html/reviews/%s/." % (specfile, user, name))
	if rc != 0:
		print "Unable to copy spec file to fedorapeople: %s" % se
		exit(1)

	print ""
	print ""

	# generate summary and header information
	print "Generating Review Request"
	print "###############################################################"
	print "Review Request: %s- %s" % (name, summary)
	print "###############################################################"
	print "Spec URL: https://%s.fedorapeople.org/reviews/%s/%s" % (user, name, os.path.basename(specfile))
	print ""
	print "SRPM URL: https://%s.fedorapeople.org/reviews/%s/%s" % (user, name, os.path.basename(srpm))
	print ""
	print "Description: %s" % description
	print ""
	print "Fedora Account System Username: %s" % user 
	print ""
	if not options.skipkoji:
		print "Koji: http://koji.fedoraproject.org/koji/taskinfo?taskID=%s" % task_id
		print ""
	print "$ rpmlint %s" % " ".join(builds)
	print rpmlint
	print "###############################################################"
	print ""
	print ""
	print "Enter values at: https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&format=fedora-review"
