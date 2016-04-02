from gofed_infra.system.models.snapshots.checker import SnapshotChecker
from gofed_lib.snapshot import Snapshot
import optparse
import logging
import re

def setOptions():

	parser = optparse.OptionParser("%prog [-l] [-v] [Godeps.json]")

	parser.add_option(
	    "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
	    help = "Verbose mode"
	)

	parser.add_option(
	    "", "", "--godeps", dest="godeps", default = "",
	    help = "Read snapshot from Godeps.json file format"
	)

	parser.add_option(
	    "", "", "--glogfile", dest="glogfile", default = "",
	    help = "Read snapshot from GLOGFILE file format"
	)

	parser.add_option(
	    "", "", "--target", dest="target", default = "Fedora:rawhide",
	    help = "Target distribution in a form OS:version, e.g. Fedora:f24. Implicitly set to Fedora:rawhide"
	)

	return parser

def checkOptions(options):

	deps_set = 0
	# at least one deps format must be set
	if options.godeps != "":
		deps_set = deps_set + 1

	if options.glogfile != "":
		deps_set = deps_set + 1

	if deps_set == 0:
		logging.error("--godeps|--glogfile not set")
		exit(1)

	# check target format
	# TODO(jchaloup): put the list of supported targets into
	# configuration file
	if not re.match(r"^Fedora:(rawhide|f2[2-5])$", options.target):
		logging.error("Target not supported")
		exit(1)

if __name__ == "__main__":


	options, args = setOptions().parse_args()

	checkOptions(options)

	if options.godeps != "":
		snapshot = Snapshot().readGodepsFile(options.godeps)
	elif options.glogfile != "":
		snapshot = Snapshot().readGLOGFILE(options.glogfile)

	target = options.target.split(":")

	SnapshotChecker().check(snapshot, target[0], target[1])

