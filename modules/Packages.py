#!/bin/python
from subprocess import Popen, PIPE
from Utils import getScriptDir
from Utils import runCommand
import re

GOLANG_PACKAGES="data/golang.packages"
script_dir = getScriptDir() + "/.."

def loadPackages():
	packages = []
	with open("%s/%s" % (script_dir, GOLANG_PACKAGES), "r") as file:
		for line in file.read().split('\n'):
			line = line.strip()
			if line == '':
				continue

			packages.append(line)
	return packages

# detect if it packages is already in pkgdb
def packageInPkgdb(pkg):
	_, _, rt = runCommand("git ls-remote http://pkgs.fedoraproject.org/cgit/" + pkg + ".git/")

	if rt == 0:
		return True

	return False

class Package:

	def __init__(self, pkg_name):
		self.pkg_name = pkg_name

	def getLatestBuilds(self, tag = 'rawhide'):
		so, se, rc = runCommand("koji -q latest-build %s %s" % (tag, self.pkg_name))
		if rc != 0:
			return []

		build = re.sub(r'[ \t]+', ' ', so.strip()).split(' ')[0]


if __name__ == "__main__":
	pkg = Package('golang-googlecode-net')
	pkg.getLatestBuilds()
