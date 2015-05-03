import sys
from modules.GoLint import GoLint
import optparse
from os import walk
from modules.Utils import FormatedPrint
from modules.Config import Config

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

	return parser

def detectFiles(info = False):
	files = []

	specfile = ""
	sources = ""
	archive = ""

	fp_obj = FormatedPrint(formated = True)

	for dirName, subdirList, fileList in walk("."):
		if dirName != ".":
			continue
		for fname in fileList:
			files.append(fname)


	for fname in files:
		if specfile == "" and fname.endswith(".spec"):
			if info:
				fp_obj.printInfo("Spec file %s detected" % fname)
			specfile = fname
			continue

		if sources == "" and fname == "sources":
			if options.info:
				fp_obj.printInfo("sources file detected")
			sources = fname
			continue

		if archive == "":
			if fname.endswith(".gz"):
				archive = fname
			if fname.endswith(".zip"):
				archive = fname
			if fname.endswith(".xz"):
				archive = name
			if archive != "":
				if options.info:
					fp_obj.printInfo("Archive %s detected" % fname)
			continue

		if specfile != "" and sources != "" and archive != "":
			break

	return (specfile, sources, archive)

if __name__ == "__main__":

	parser = setOptions()
	options, args = parser.parse_args()

	specfile, sources, archive = detectFiles(options.info)

	# if options only files detection
	if options.info:
		exit(0)

	if options.archive:
		archive = options.archive

	if options.spec:
		specfile = options.spec

	if options.sources:
		sources = options.sources

	if archive == "":
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
	if not obj.test():
		print obj.getError()

	err_cnt = obj.getErrorCount()
	warn_cnt = obj.getWarningCount()

	print "1 golang specfile checked; %s errors, %s warnings." % (err_cnt, warn_cnt)