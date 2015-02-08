#!/bin/python
from subprocess import Popen, PIPE
from Utils import getScriptDir
from Utils import runCommand

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
	cmd = "git ls-remote http://pkgs.fedoraproject.org/cgit/" + pkg + ".git/"
	p = Popen(cmd , shell=True, stdout=PIPE, stderr=PIPE)
	out, err = p.communicate()

	if p.returncode == 0:
		return True

	return False
