import os
import optparse
from modules.Tools import MultiCommand
from modules.Config import Config

if __name__ == "__main__":

	parser = optparse.OptionParser("%prog")

	parser.add_option(
	    "", "", "--gcp", dest="gcp", action = "store_true", default = False,
	    help = "git cherry-pick master all branches"
	)

	parser.add_option(
	    "", "", "--git-reset", dest="greset", action = "store_true", default = False,
	    help = "git reset --hard all branches to remotes/origin/*"
	)

	parser.add_option(
	    "", "", "--pull", dest="pull", action = "store_true", default = False,
	    help = "git pull all branches"
	)

	parser.add_option(
	    "", "", "--push", dest="push", action = "store_true", default = False,
	    help = "fedpkg push all branches"
	)

	parser.add_option(
	    "", "", "--scratch", dest="scratch", action = "store_true", default = False,
	    help = "fedpkg scratch-build all branches"
	)

	parser.add_option(
	    "", "", "--build", dest="build", action = "store_true", default = False,
	    help = "fedpkg build all branches"
	)

	parser.add_option(
	    "", "", "--update", dest="update", action = "store_true", default = False,
	    help = "fedpkg update all branches"
	)

	parser.add_option(
	    "", "", "--branches", dest="branches", default = "",
	    help = "use only listed branches"
	)

	parser.add_option(
	    "", "", "--ebranches", dest="ebranches", default = "",
	    help = "use all branches except listed ones"
	)

	parser.add_option(
	    "", "", "--dry", dest="dry", action = "store_true", default = False,
	    help = "run the command in dry mode"
	)

	parser.add_option(
	    "", "", "--verbose", dest="debug", action = "store_true", default = False,
	    help = "be more verbose "
	)

	options, args = parser.parse_args()

	branches = Config().getBranches()
	if options.branches != "":
		bs = filter(lambda b: b != "", options.branches.split(","))
		for branch in bs:
			if branch in branches:
				continue

			print "%s branch not in a list of all branches" % branch
			exit(1)

		branches = bs

	if options.ebranches != "":
		ebs = filter(lambda b: b != "", options.ebranches.split(","))
		for branch in ebs:
			if branch in branches:
				continue

			print "%s branch not in a list of all branches" % branch
			exit(1)
	
		branches = sorted(list(set(branches) - set(ebs)))

	mc = MultiCommand(debug=options.debug, dry=options.dry)

	if options.gcp:
		mc.cherryPickMaster(branches)
	if options.greset:
		mc.resetBranchesToOrigin(branches)
	if options.pull:
		mc.pullBranches(branches)
	if options.push:
		mc.pushBranches(branches)
	if options.scratch:
		if mc.scratchBuildBranches(branches):
			exit(0)
		else:
			exit(1)
	if options.build:
		if mc.buildBranches(branches):
			exit(0)
		else:
			exit(1)
	if options.update:
		if options.branches == "":
			branches = Config().getUpdates()

		mc.updateBranches(branches)

