import logging
import os

from gofedlib.logger.logger import Logger
from gofedlib.distribution.clients.koji.client import KojiClient
from gofedlib.distribution.clients.koji.fakeclient import FakeKojiClient
from gofedlib.distribution.clients.pkgdb.client import PkgDBClient
from gofedlib.distribution.clients.pkgdb.fakeclient import FakePkgDBClient
from gofedinfra.system.models.ecosnapshots.distributionsnapshotchecker import DistributionSnapshotChecker
from gofedlib.distribution.distributionnameparser import DistributionNameParser

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
	# - where to store snapshots? under gofedlib or gofedinfra? I am inclined to use gofed_data to store all artefacts and other data kinds
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
