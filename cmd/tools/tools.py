import os
from gofed.modules.Tools import MultiCommand
from gofed.modules.Config import Config
import sys
from gofed.modules.FilesDetector import FilesDetector
from gofed.modules.SpecParser import SpecParser
from gofed.modules.Utils import FormatedPrint

import logging
logging.basicConfig(level=logging.INFO)

from cmdsignature.parser import CmdSignatureParser
from gofed_lib.utils import getScriptDir

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/tools-global.yml" % (cur_dir)

	program_name = os.path.basename(sys.argv[0])
	provider = ""
	subcmd_flags = []

	if program_name == "tools.py":
		parser = CmdSignatureParser([gen_flags, "%s/tools.yml" % (cur_dir)])
	else:
		parser = CmdSignatureParser([gen_flags])

	parser.generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()

	if program_name == "build":
		options.build = True
	elif program_name == "bbobranches":
		options.bbo = True
	elif program_name == "gcpmaster":
		options.gcp = True
	elif program_name == "pull":
		options.pull = True
	elif program_name == "push":
		options.push = True
	elif program_name == "scratch-build":
		options.scratch = True
	elif program_name == "update":
		options.update = True

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
