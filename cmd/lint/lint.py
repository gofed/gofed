import sys
from gofed.modules.GoLint import GoLint
import os
from os import walk
from gofed.modules.Utils import FormatedPrint
from gofed.modules.Config import Config
from gofed.modules.FilesDetector import FilesDetector

from cmdsignature.parser import CmdSignatureParser
from gofedlib.utils import getScriptDir

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/%s.yml" % (cur_dir, os.path.basename(__file__).split(".")[0])

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	fd = FilesDetector()
	fd.detect()
	specfile = fd.getSpecfile()
	sources = fd.getSources()
	archive = fd.getArchive()

	# if options only files detection
	if options.info:
		exit(0)

	if options.archive:
		archive = options.archive

	if options.spec:
		specfile = options.spec

	if options.sources:
		sources = options.sources

	fp_obj = FormatedPrint(formated=True)

	if options.sourcecodedirectory == "" and archive == "":
		fp_obj.printError("archive not set")
		exit(1)

	if specfile == "":
		fp_obj.printError("specfile not set")
		exit(1)

	if not options.scanalldirs:
		noGodeps = Config().getSkippedDirectories()
	else:
		noGodeps = []

	if options.skipdirs:
		for dir in options.skipdirs.split(','):
			dir = dir.strip()
			if dir == "":
				continue
			noGodeps.append(dir)

	obj = GoLint(specfile, sources, archive, options.verbose, noGodeps = noGodeps)
	if not obj.test(options.sourcecodedirectory):
		print obj.getError()

	err_cnt = obj.getErrorCount()
	warn_cnt = obj.getWarningCount()

	print "1 golang specfile checked; %s errors, %s warnings." % (err_cnt, warn_cnt)
