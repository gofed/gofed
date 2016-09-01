import os
import logging
import time
from gofed_lib.logger.logger import Logger

from gofed_infra.system.models.ecomanagement.fetchers.distributionbuilds import DistributionBuildsFetcher
from gofed_lib.distribution.clients.pkgdb.client import PkgDBClient
from gofed_lib.distribution.clients.pkgdb.fakeclient import FakePkgDBClient
from gofed_lib.distribution.distributionnameparser import DistributionNameParser

from cmdsignature.parser import CmdSignatureParser
from gofed_lib.utils import getScriptDir

def checkOptions(options):
	if options.atmost < options.atleast:
		logging.error("'atmost >= atleast' does not hold")
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

	if options.dryrun:
		fetcher = DistributionBuildsFetcher(FakePkgDBClient(), True)
	else:
		fetcher = DistributionBuildsFetcher(PkgDBClient(), False)

	if options.atleast > 0:
		fetcher.fetch(distributions, since = int(time.time()) - int(options.atmost)*86400, to = int(time.time()) - int(options.atleast)*86400)
	else:
		fetcher.fetch(distributions, since = int(time.time()) - int(options.atmost)*86400)

