# TODO
# [  ] - add check I am in a package folder

from gofed.modules.Tools import PhaseMethods
import os
from gofed.modules.Config import Config

from cmdsignature.parser import CmdSignatureParser
from gofed_lib.utils import getScriptDir

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/%s.yml" % (cur_dir, os.path.basename(__file__).split(".")[0])

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()


	pm = PhaseMethods(dry=options.dryrun, debug=options.verbose, new=options.new)

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

	if options.endwithscratch:
		pm.stopWithScratchBuild()
	elif options.endwithpush:
		pm.stopWithPush()
	elif options.endwithbuild:
		pm.stopWithBuild()
	elif options.endwithupdate:
		pm.stopWithUpdate()
	elif options.endwithoverride:
		pm.stopWithOverride()

	pm.run()

