# TODO
# [  ] - add check I am in a package folder

from gofed.modules.Tools import PhaseMethods
import optparse
from gofed.modules.Config import Config

if __name__ == "__main__":

	parser = optparse.OptionParser()

	parser.add_option(
	    "", "", "--scratch", dest="scratch", action = "store_true", default = False,
	    help = "Start from scratch build"
	)

	parser.add_option(
	    "", "", "--push", dest="push", action = "store_true", default = False,
	    help = "Start from push"
	)

	parser.add_option(
	    "", "", "--build", dest="build", action = "store_true", default = False,
	    help = "Start from build"
	)

	parser.add_option(
	    "", "", "--update", dest="update", action = "store_true", default = False,
	    help = "Start from update"
	)

	parser.add_option(
	    "", "", "--override", dest="override", action = "store_true", default = False,
	    help = "Start from override"
	)

	parser.add_option(
	    "", "", "--dry-run", dest="dry", action = "store_true", default = False,
	    help = "Use dry mode"
	)

	parser.add_option(
	    "", "-v", "--verbose", dest="debug", action = "store_true", default = False,
	    help = "Be more verbose"
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
	    "", "", "--endwithscratch", dest="endscratch", action = "store_true", default = False,
	    help = "stop wizard after scratch phase"
	)

	parser.add_option(
	    "", "", "--endwithpush", dest="endpush", action = "store_true", default = False,
	    help = "stop wizard after push phase"
	)

	parser.add_option(
	    "", "", "--endwithbuild", dest="endbuild", action = "store_true", default = False,
	    help = "stop wizard after build phase"
	)

	parser.add_option(
	    "", "", "--endwithupdate", dest="endupdate", action = "store_true", default = False,
	    help = "stop wizard after update phase"
	)

	parser.add_option(
	    "", "", "--endwithoverride", dest="endoverride", action = "store_true", default = False,
	    help = "stop wizard after override phase"
	)

	parser.add_option(
	    "", "", "--new", dest="new", action = "store_true", default = False,
	    help = "Generate update for new package"
	)

	options, args = parser.parse_args()

	pm = PhaseMethods(dry=options.dry, debug=options.debug, new=options.new)

	# check branches
	if options.branches:
		branches = Config().getBranches()
		sb = filter(lambda b: b != "", options.branches.split(","))
		for b in sb:
			if b not in branches:
				print "%s branch not in common branches" % b
				exit(1)
		pm.setBranches(sorted(sb))

	if options.ebranches:
		branches = Config().getBranches()
		sb = filter(lambda b: b != "", options.ebranches.split(","))
		branches = list(set(branches) - set(sb))
		pm.setBranches(sorted(branches))

        if options.master:
		branches = ["master"]
		pm.setBranches(branches)

	if options.scratch:
		pm.startWithScratchBuild()
	elif options.push:
		pm.startWithPush()
	elif options.build:
		pm.startWithBuild()
	elif options.update:
		pm.startWithUpdate()
	elif options.override:
		pm.startWithOverride()
	else:
		print "Missing options, run --help."
		exit(1)

	if options.endscratch:
		pm.stopWithScratchBuild()
	elif options.endpush:
		pm.stopWithPush()
	elif options.endbuild:
		pm.stopWithBuild()
	elif options.endupdate:
		pm.stopWithUpdate()
	elif options.endoverride:
		pm.stopWithOverride()

	pm.run()

