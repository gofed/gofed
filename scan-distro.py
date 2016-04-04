import optparse
import logging
import re
import json

from gofed_lib.kojiclient import FakeKojiClient, KojiClient
from gofed_lib.pkgdb.client import FakePkgDBClient
from gofed_lib.distributionsnapshot import DistributionSnapshot
from gofed_lib.eco.capturer import EcoCapturer
from gofed_infra.system.models.ecosnapshots.distributionsnapshotchecker import DistributionSnapshotChecker

#logging.basicConfig(level=logging.INFO)

def setOptions():

	parser = optparse.OptionParser("%prog [-l] [-v] [Godeps.json]")

	parser.add_option(
	    "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
	    help = "Verbose mode"
	)

	parser.add_option(
	    "", "", "--target", dest="target", default = "Fedora:rawhide",
	    help = "Target distribution in a form OS:version, e.g. Fedora:f24. Implicitly set to Fedora:rawhide"
	)

	parser.add_option(
	    "", "-f", "--full-check", dest="fullcheck", action = "store_true", default = False,
	    help = "Checkout all builds in requested distributions (the current snapshot is ignored)"
	)

	parser.add_option(
	    "", "-s", "--skip-failed", dest="skipfailed", action = "store_true", default = False,
	    help = "If any scan in given distribution fails, don't update its latest snapshot"
	)

	parser.add_option(
	    "", "", "--custom-packages", dest="custompackages", default = "",
	    help = "Comma separated string of golang packages not prefixed with golang-*, e.g. etcd,runc"
	)

	return parser

def checkOptions(options):

	# check target format
	# TODO(jchaloup): put the list of supported targets into
	# configuration file
	if not re.match(r"^Fedora:(rawhide|f2[2-5])(,Fedora:(rawhide|f2[2-5]))*$", options.target):
		logging.error("Target not supported")
		exit(1)

if __name__ == "__main__":
	options, args = setOptions().parse_args()

	checkOptions(options)

	distributions = []
	for distro in options.target.split(","):
		parts = distro.split(":")
		distributions.append({"product": parts[0], "version": parts[1]})

	custom_packages = options.custompackages.split(",")

	# TODO(jchaloup):
	# - where to store snapshots? under gofed_lib or gofed_infra? I am inclined to use gofed_data to store all artefacts and other data kinds
	#   as each snapshot is determined by timestamp, it can not be stored as artefacts are (without introducing additional list of snashots)
	#   Other thought (once the storage can provide a list of artefact based on a partial key, repo artefact and cache can be regenerated
	#   based on commits in a storage rather then on a list of commits retrieved from repository.
	#   Temporary, save the snapshot into db (generated artefact for it) and always replace distribution artefact with the latest snapshot.
	#   Once the storage provides list functionality, just retrieve the snapshot with the biggest timestamp (for given distribution).
	# - introduce EcoScannerAct updating the latest snapshot and scan of the new rpms. Later, add support for upstream repositories as well.
	#

	DistributionSnapshotChecker(
		KojiClient(),
		FakePkgDBClient()
	).check(
		distributions,
		custom_packages,
		full_check = options.fullcheck,
		skip_failed = options.skipfailed
	)
