from gofedinfra.system.models.snapshots.reconstructor import SnapshotReconstructor
from gofedlib.go.importpath.parserbuilder import ImportPathParserBuilder
from gofedlib.providers.providerbuilder import ProviderBuilder
import json
import optparse
import sys
import logging
import os

from cmdsignature.parser import CmdSignatureParser
from gofedlib.utils import getScriptDir

# TODO(jchaloup):
# - add support for construction of snaphost from given directory with given timestamp
# - add support for complete snapshot (with all mains and tests), devel is default
# - add support for workspace clean called at the end (clean content of resource_client and resource_provider)

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/%s.yml" % (cur_dir, os.path.basename(__file__).split(".")[0])

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	if options.verbose:
		logging.basicConfig(level=logging.WARNING)
	else:
		logging.basicConfig(level=logging.ERROR)


	# mains?
	mains = []

	if options.mainpackages != "":
		mains = options.mains.split(",")

	# parse repository
	ipparser = ImportPathParserBuilder().buildWithLocalMapping()
	pparser = ProviderBuilder().buildUpstreamWithLocalMapping()

	# TODO(jchaloup): catch ValueError exception
	repository = pparser.parse(options.repository).signature()

	snapshot = SnapshotReconstructor().reconstruct(options.repository, options.commit, options.ipprefix, mains = mains, tests=options.unittests).snapshot()

	if options.godeps:
		print json.dumps(snapshot.Godeps())
	elif options.glogfile:
		print snapshot.GLOGFILE()
	elif options.glidefile:
		print snapshot.Glide()
