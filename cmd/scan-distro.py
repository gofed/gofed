import logging
import optparse

from gofed_lib.logger.logger import Logger
from gofed_lib.distribution.clients.koji.client import KojiClient
from gofed_lib.distribution.clients.koji.fakeclient import FakeKojiClient
from gofed_lib.distribution.clients.pkgdb.client import PkgDBClient
from gofed_lib.distribution.clients.pkgdb.fakeclient import FakePkgDBClient
from gofed_infra.system.models.ecosnapshots.distributionsnapshotchecker import DistributionSnapshotChecker
from gofed_lib.distribution.distributionnameparser import DistributionNameParser

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

	parser.add_option(
	    "", "", "--blacklist", dest="blacklist", default = "",
	    help = "Comma separated string of packages to be skipped, e.g. etcd,runc"
	)

	parser.add_option(
	    "", "", "--dry-run", dest="dryrun", action = "store_true", default = False,
	    help = "Run dry scan"
	)

	return parser

if __name__ == "__main__":
	options, args = setOptions().parse_args()

	distributions = []
	try:
		for distro in options.target.split(","):
			distributions.append(DistributionNameParser().parse(distro).signature())
	except ValueError as e:
		logging.error(e)
		exit(1)

	Logger.set(options.verbose)

	custom_packages = options.custompackages.split(",")
	blacklist = options.blacklist.split(",")

	# TODO(jchaloup):
	# - where to store snapshots? under gofed_lib or gofed_infra? I am inclined to use gofed_data to store all artefacts and other data kinds
	#   as each snapshot is determined by timestamp, it can not be stored as artefacts are (without introducing additional list of snashots)
	#   Other thought (once the storage can provide a list of artefact based on a partial key, repo artefact and cache can be regenerated
	#   based on commits in a storage rather then on a list of commits retrieved from repository.
	#   Temporary, save the snapshot into db (generated artefact for it) and always replace distribution artefact with the latest snapshot.
	#   Once the storage provides list functionality, just retrieve the snapshot with the biggest timestamp (for given distribution).
	# - introduce EcoScannerAct updating the latest snapshot and scan of the new rpms. Later, add support for upstream repositories as well.
	#

	if options.dryrun:
		checker = DistributionSnapshotChecker(
			FakeKojiClient(),
			FakePkgDBClient(),
			True
		)
	else:
		checker = DistributionSnapshotChecker(
			KojiClient(),
			PkgDBClient(),
			False
		)

	checker.check(
		distributions,
		custom_packages,
		blacklist,
		full_check = options.fullcheck,
		skip_failed = options.skipfailed
	)
