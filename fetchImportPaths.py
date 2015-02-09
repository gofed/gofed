#!/bin/python

from modules.Packages import Package
from modules.Packages import loadPackages
import optparse

def displayImportPaths(data):
	for devel in data:
		paths = ",".join(data[devel]['provides'])
		print "Provides:%s:%s" % (devel, paths)

def displayImportedPaths(data):
	for devel in data:
		paths = ",".join(data[devel]['provides'])
		print "Imports:%s:%s" % (devel, paths)

if __name__ == "__main__":
	packages = loadPackages()

	for package in packages:
		print "# Scanning %s ... " % package
		pkg = Package(package)
		info = pkg.getInfo()
		displayImportPaths(info)
		displayImportedPaths(info)

