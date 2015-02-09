#!/bin/python

from modules.Packages import getPackagesFromPkgDb, loadPackages

import optparse

def getPkgs():
	pkgs_pkgdb = getPackagesFromPkgDb()
	pkgs_local = loadPackages()

	# Any new or removed packages
	set_pkgdb = set(pkgs_pkgdb)
	set_local = set(pkgs_local)

	return set_pkgdb, set_local

def printPkgs(pkgs):
	for pkg in pkgs:
		print pkg

if __name__ == "__main__":

	parser = optparse.OptionParser("%prog [-n] [-r]")

	parser.add_option(
	    "", "-n", "--new", dest="new", action = "store_true", default = False,
	    help = "Scan for new golang packages"
	)

	parser.add_option(
	    "", "-r", "--removed", dest="removed", action = "store_true", default = False,
	    help = "Scan for removed golang packages"
	)

	options, args = parser.parse_args()

	# new packages
	if options.new:
		set_pkgdb, set_local = getPkgs()
		printPkgs(list(set_pkgdb - set_local))
	elif options.removed:
		set_pkgdb, set_local = getPkgs()
		printPkgs(list(set_local - set_pkgdb))
	else:
		print "Synopsis: [-n] [-r]"
