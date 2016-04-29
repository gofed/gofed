import os
import optparse
from modules.Tools import MultiCommand
from modules.Config import Config
import sys
from modules.FilesDetector import FilesDetector
from modules.SpecParser import SpecParser
from modules.Utils import FormatedPrint

import logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":

	parser = optparse.OptionParser("%prog")

	sln = not (os.path.basename(sys.argv[0]) == "tools.py")

	SH = optparse.SUPPRESS_HELP

	parser.add_option(
	    "", "", "--gcp", dest="gcp", action = "store_true", default = False,
	    help = SH if sln else "git cherry-pick master all branches"
	)

	parser.add_option(
	    "", "", "--merge-master", dest="mergemaster", action = "store_true", default = False,
	    help = SH if sln else "git merge master all branches"
	)

	parser.add_option(
	    "", "", "--git-reset", dest="greset", action = "store_true", default = False,
	    help = SH if sln else "git reset --hard all branches to remotes/origin/*"
	)

	parser.add_option(
	    "", "", "--from", dest="commit", default = "",
	    help = SH if sln else "git cherry-pick master starting from COMMIT, used with --gcp option"
	)

	parser.add_option(
	    "", "", "--pull", dest="pull", action = "store_true", default = False,
	    help = SH if sln else "git pull all branches"
	)

	parser.add_option(
	    "", "", "--push", dest="push", action = "store_true", default = False,
	    help = SH if sln else "fedpkg push all branches"
	)

	parser.add_option(
	    "", "", "--scratch", dest="scratch", action = "store_true", default = False,
	    help = SH if sln else "fedpkg scratch-build all branches"
	)

	parser.add_option(
	    "", "", "--build", dest="build", action = "store_true", default = False,
	    help = SH if sln else "fedpkg build all branches"
	)

	parser.add_option(
	    "", "", "--update", dest="update", action = "store_true", default = False,
	    help = SH if sln else "fedpkg update all branches"
	)

	parser.add_option(
	    "", "", "--bbo", dest="bbo", action="store_true", default = False,
	    help = SH if sln else "buildroot override build for branches"
	)

	parser.add_option(
	    "", "", "--wait", dest="wait", action = "store_true", default = False,
	    help = SH if sln else "wait for buildroot override, can be used with --bbo"
	)

	parser.add_option(
	    "", "", "--waitbbo", dest="waitbbo", action = "store_true", default = False,
	    help = SH if sln else "wait for buildroot override"
	)

	parser.add_option(
	    "", "", "--master", dest="master", action = "store_true", default = False,
	    help = "use only master branche. If --branches or --ebranches option use, --master has higher priority"
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
	    "", "", "--dry-run", dest="dry", action = "store_true", default = False,
	    help = "run the command in dry mode"
	)

	parser.add_option(
	    "", "-v", "--verbose", dest="debug", action = "store_true", default = False,
	    help = "be more verbose"
	)

	parser.add_option(
	    "", "", "--new", dest="new", action = "store_true", default = False,
	    help = "Generate update for new package"
	)

	options, args = parser.parse_args()

	fp_obj = FormatedPrint(formated=False)

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

        if options.master:
		branches = ["master"]

	mc = MultiCommand(debug=options.debug, dry=options.dry)

	if options.gcp:
		err = mc.cherryPickMaster(branches, start_commit=options.commit, verbose=options.debug)
		if err and err != []:
			print "\n".join(err)

	if options.mergemaster:
		mc.mergeMaster(branches)
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
		if options.branches == "" and options.ebranches == "":
			branches = Config().getUpdates()
		else:
			branches = list(set(branches) & set(Config().getUpdates()))

		mc.updateBuilds(branches, new = options.new)

	if options.bbo or options.waitbbo or options.wait:
		# if no build specified, detect it from the current directory
		if len(args) < 1:
			fd = FilesDetector()
			fd.detect()
			specfile = fd.getSpecfile()
			if specfile == "":
				sys.stderr.write("Missing build name\n")
				exit(1)

			fp_obj.printInfo("Spec file detected: %s" % specfile)
			sp_obj = SpecParser(specfile)
			if not sp_obj.parse():
				sys.stderr.write(sp_obj.getError())
				exit(1)

			name = sp_obj.getTag("name")
			version = sp_obj.getTag("version")
			release = ".".join( sp_obj.getTag("release").split('.')[:-1])
			# N-V-R without tag (e.g. no fc22)
			build = "%s-%s-%s" % (name, version, release)
			fp_obj.printInfo("Build name constructed: %s" % build)
		else:
			build = args[0]

		if options.branches == "" and options.ebranches == "":
			branches = Config().getOverrides()
		else:
			branches = list(set(branches) & set(Config().getOverrides()))

		if options.bbo:
			done = mc.overrideBuilds(branches)
			if done and options.wait:
				mc.waitForOverrides(branches, build)

		if options.waitbbo or options.wait:
			mc.waitForOverrides(branches, build)
