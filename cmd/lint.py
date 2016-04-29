import sys
from gofed.modules.GoLint import GoLint
import optparse
from os import walk
from gofed.modules.Utils import FormatedPrint
from gofed.modules.Config import Config
from gofed.modules.FilesDetector import FilesDetector

def setOptions():
	parser = optparse.OptionParser("%prog [-a] [-c] [-d [-v]] [directory]")

	parser.add_option(
	    "", "-d", "--detect", dest="detect", action = "store_true", default = False,
	    help = "Detect spec file and tarball (and sources if in Fedora repository) in the current directory"
	)

	parser.add_option(
            "", "-s", "--spec", dest="spec", default = "",
            help = "Set spec file"
        )

	parser.add_option(
            "", "", "--sources", dest="sources", default = "",
            help = "Set sources file (optional)"
        )

	parser.add_option(
            "", "-a", "--archive", dest="archive", default = "",
            help = "Set archive file"
        )

	parser.add_option(
            "", "-i", "--info", dest="info", action = "store_true", default = False,
            help = "Displays only detected files (only with -d option)"
        )

	parser.add_option(
            "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
            help = "Verbose mode"
        )

	parser.add_option(
            "", "", "--scan-all-dirs", dest="scanalldirs", action = "store_true", default = False,
            help = "Scan all dirs, including Godeps directory"
        )

	parser.add_option(
            "", "", "--skip-dirs", dest="skipdirs", default = "",
            help = "Scan all dirs except specified via SKIPDIRS. Directories are comma separated list."
        )

	parser.add_option(
            "", "", "--source-code-directory", dest="sourcecodedirectory", default = "",
            help = "Check source code directory instead of extracted tarball"
        )

	return parser

if __name__ == "__main__":

	parser = setOptions()
	options, args = parser.parse_args()

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
