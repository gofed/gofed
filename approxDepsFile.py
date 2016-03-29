from gofed_infra.system.models.snapshots.reconstructor import SnapshotReconstructor
from gofed_lib.importpathparserbuilder import ImportPathParserBuilder
import json
import optparse
import sys
import logging

# TODO(jchaloup):
# - add support for construction of snaphost from given directory with given timestamp
# - add support for complete snapshot (with all mains and tests), devel is default
# - add support for workspace clean called at the end (clean content of resource_client and resource_provider)

def setOptions():
	parser = optparse.OptionParser("%prog [-a] [-c] [-d [-v]] [directory]")

	parser.add_option_group( optparse.OptionGroup(parser, "directory", "Directory to inspect. If empty, current directory is used.") )

	parser.add_option(
	    "", "", "--godeps", dest="godeps", action = "store_true", default = False,
	    help = "Display dependencies as Godeps.json"
	)

	parser.add_option(
	    "", "", "--glogfile", dest="glogfile", action = "store_true", default = False,
	    help = "Display dependencies as GLOGFILE"
	)

	parser.add_option(
            "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
            help = "Verbose mode"
        )

	parser.add_option(
            "", "", "--repository", dest="repository", default = "",
            help = "Repository"
        )

	parser.add_option(
            "", "", "--commit", dest="commit", default = "",
            help = "Repository commit"
        )

	parser.add_option(
            "", "", "--ipprefix", dest="ipprefix", default = "",
            help = "Import path prefix"
        )

	parser.add_option(
            "", "-t", "--unit-tests", dest="tests", action = "store_true", default = False,
            help = "Cover dependencies of unit tests as well"
        )

	parser.add_option(
            "", "-m", "--main-packages", dest="mains", default = "",
            help = "Comma separated file list of main packages specified from repository root directory (without leading '/')"
        )

	return parser

def validateOptions(options):
	if options.commit == "":
		sys.stderr.write("Commit missing\n")
		exit(1)

	if options.ipprefix == "":
		sys.stderr.write("Import path prefix missing\n")
		exit(1)

	if options.repository == "":
		sys.stderr.write("Repository missing\n")
		exit(1)

	# at least godeps or glogfile must be specified
	if options.godeps == False and options.glogfile == False:
		sys.stderr.write("Output format missing\n")
		exit(1)

if __name__ == "__main__":

	parser = setOptions()
	options, args = parser.parse_args()
	validateOptions(options)

	if options.verbose:
		logging.basicConfig(level=logging.WARNING)
	else:
		logging.basicConfig(level=logging.ERROR)


	# mains?
	mains = []
	if options.mains != "":
		mains = options.mains.split(",")

	# parse repository
	ipparser = ImportPathParserBuilder().buildWithLocalMapping()
	# TODO(jchaloup): catch ValueError exception
	repository = ipparser.parse(options.repository).getProviderSignature()

	snapshot = SnapshotReconstructor().reconstruct(repository, options.commit, options.ipprefix, mains = mains, tests=options.tests).snapshot()

	if options.godeps:
		print json.dumps(snapshot.Godeps())
	elif options.glogfile:
		print snapshot.GLOGFILE()
