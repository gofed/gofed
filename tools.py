import os
import optparse
from modules.Tools import cherryPickMaster, resetBranchesToOrigin
from modules.Tools import pullBranches, pushBranches, updateBranches
from modules.Tools import scratchBuildBranches, buildBranches
from modules.Config import Config

if __name__ == "__main__":

	parser = optparse.OptionParser("%prog")

	parser.add_option(
	    "", "", "--gcp", dest="gcp", action = "store_true", default = False,
	    help = "git cherry-pick master all branches"
	)

	parser.add_option(
	    "", "", "--git-reset", dest="greset", action = "store_true", default = False,
	    help = "git reset --hard all branches to remoter/origin/*"
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

	options, args = parser.parse_args()

	branches = Config().getBranches()
	if options.branches != "":
		bs = filter(lambda b: b != "", options.branches.split(","))
		for branch in bs:
			if branch in branches:
				continue

			print "%s branch in a list of all branches" % branch
			exit(1)

		branches = bs

	if options.gcp:
		cherryPickMaster(branches)
	if options.greset:
		resetBranchesToOrigin(branches)
	if options.pull:
		pullBranches(branches)
	if options.push:
		pushBranches(branches)
	if options.scratch:
		if scratchBuildBranches(branches):
			exit(0)
		else:
			exit(1)
	if options.build:
		if buildBranches(branches):
			exit(0)
		else:
			exit(1)
	if options.update:
		if options.branches == "":
			branches = Config().getUpdates()

		updateBranches(branches)

