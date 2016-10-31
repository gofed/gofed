from gofedinfra.system.models.snapshots.checker import SnapshotChecker
from gofedlib.go.snapshot import Snapshot
import optparse
import logging
import re

from cmdsignature.parser import CmdSignatureParser
from gofedlib.utils import getScriptDir
import os

def checkOptions(options):

	# check target format
	# TODO(jchaloup): put the list of supported targets into
	# configuration file
	if not re.match(r"^Fedora:(rawhide|f2[2-5])$", options.target):
		logging.error("Target not supported")
		exit(1)

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/%s.yml" % (cur_dir, os.path.basename(__file__).split(".")[0])

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	checkOptions(options)

	if options.godeps != "":
		snapshot = Snapshot().readGodepsFile(options.godeps)
	elif options.glidefile != "":
		snapshot = Snapshot().readGlideLockFile(options.glidefile)
	elif options.glogfile != "":
		snapshot = Snapshot().readGLOGFILE(options.glogfile)

	target = options.target.split(":")

	SnapshotChecker(options.dryrun).check(snapshot, target[0], target[1])

