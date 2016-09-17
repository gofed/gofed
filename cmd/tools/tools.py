#!/bin/python

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
from gofedlib.utils import getScriptDir

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/tools-global.yml" % (cur_dir)

	program_name = os.path.basename(sys.argv[0])
	provider = ""
	subcmd_flags = []

	if program_name == "tools.py":
		parser = CmdSignatureParser([gen_flags, "%s/tools.yml" % (cur_dir)])
	elif program_name == "bbobranches":
		parser = CmdSignatureParser([gen_flags, "%s/bbo.yml" % (cur_dir)])
	elif program_name == "update":
		parser = CmdSignatureParser([gen_flags, "%s/update.yml" % (cur_dir)])
	else:
		parser = CmdSignatureParser([gen_flags])

	parser.generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
        args = parser.args()

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

	mc = MultiCommand(debug=options.verbose, dry=options.dryrun)

	build_flag = False
	bbo_flag = False
	gcp_flag = False
	pull_flag = False
	push_flag = False
	scratch_flag = False
	update_flag = False
	mergemaster_flag = False
	gitreset_flag = False
	bbo_flag = False
	waitbbo_flag = False
	wait_flag = False

	if program_name == "build":
		build_flag = True
	elif program_name == "bbobranches":
		bbo_flag = True
	elif program_name == "gcpmaster":
		gcp_flag = True
	elif program_name == "pull":
		pull_flag = True
	elif program_name == "push":
		push_flag = True
	elif program_name == "scratch-build":
		scratch_flag = True
	elif program_name == "update":
		update_flag = True

	if program_name == "tools.py":
		if options.gcp:
			gcp_flag = True
		if options.mergemaster:
			mergemaster_flag = True
		if options.gitreset:
			gitreset_flag = True
		if options.pull:
			pull_flag = True
		if options.push:
			push_flag = True
		if options.scratch:
			scratch_flag = True
		if options.build:
			build_flag = True
		if options.update:
			update_flag = True
		if options.bbo:
			bbo_flag = True
		if options.waitbbo:
			waitbbo_flag = True
		if options.wait:
			wait_flag = True

	if gcp_flag:
		err = mc.cherryPickMaster(branches, start_commit=options.commit, verbose=options.verbose)
		if err and err != []:
			print "\n".join(err)

	if mergemaster_flag:
		mc.mergeMaster(branches)
	if gitreset_flag:
		mc.resetBranchesToOrigin(branches)
	if pull_flag:
		mc.pullBranches(branches)
	if push_flag:
		mc.pushBranches(branches)
	if scratch_flag:
		if mc.scratchBuildBranches(branches):
			exit(0)
		else:
			exit(1)
	if build_flag:
		if mc.buildBranches(branches):
			exit(0)
		else:
			exit(1)
	if update_flag:
		if options.branches == "" and options.ebranches == "":
			branches = Config().getUpdates()
		else:
			branches = list(set(branches) & set(Config().getUpdates()))

		mc.updateBuilds(branches, new = options.new)

	if bbo_flag or waitbbo_flag or wait_flag:
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

		if bbo_flag:
			done = mc.overrideBuilds(branches)
			if done and wait_flag:
				mc.waitForOverrides(branches, build)

		if waitbbo_flag or wait_flag:
			mc.waitForOverrides(branches, build)
