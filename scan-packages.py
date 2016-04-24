import optparse
import logging
import time
from gofed_lib.logger.logger import Logger

from gofed_infra.system.models.ecomanagement.fetchers.distributionbuilds import DistributionBuildsFetcher
from gofed_lib.distribution.clients.pkgdb.client import FakePkgDBClient, PkgDBClient
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
	    "", "", "--atmost", dest="atmost", default = "1",
	    help = "Scan packages that has at least one build at most number of days old. Default 1 day."
	)

	parser.add_option(
	    "", "", "--atleast", dest="atleast", default = "0",
	    help = "Scan packages that has at least one build at least number of days old. Default 0 day."
	)

	return parser

def checkOptions(options):

	try:
		int(options.atmost)
	except ValueError:
		logging("atmost must be integer")
		exit(1)

	try:
		int(options.atleast)
	except ValueError:
		logging("atleast must be integer")
		exit(1)

	if options.atmost < 0:
		logging.error("atmost must be non-negative")
		exit(1)

	if options.atleast < 0:
		logging.error("atleast must be non-negative")
		exit(1)

	if options.atmost < options.atleast:
		logging.error("'atmost >= atleast' does not hold")
		exit(1)

if __name__ == "__main__":
	options, args = setOptions().parse_args()

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

	if options.atleast > 0:
		DistributionBuildsFetcher(PkgDBClient()).fetch(distributions, since = int(time.time()) - int(options.atmost)*86400, to = int(time.time()) - int(options.atleast)*86400)
	else:
		DistributionBuildsFetcher(PkgDBClient()).fetch(distributions, since = int(time.time()) - int(options.atmost)*86400)

