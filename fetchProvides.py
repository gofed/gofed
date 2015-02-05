#!/bin/python

from subprocess import PIPE
from subprocess import Popen
import tempfile
import specParser
import os

script_dir = os.path.dirname(os.path.realpath(__file__))

def runCommand(cmd):
        #cmd = cmd.split(' ')
        process = Popen(cmd, stderr=PIPE, stdout=PIPE, shell=True)
        rt = process.returncode
        stdout, stderr = process.communicate()
        return stdout, stderr, rt

def fetchProvides(pkg, branch):
	"""Fetch a spec file from pkgdb and get provides from all its [sub]packages

	Keyword arguments:
	pkg -- package name
	branch -- branch name
	"""
	f = tempfile.NamedTemporaryFile(delete=True)
	runCommand("curl http://pkgs.fedoraproject.org/cgit/%s.git/plain/%s.spec > %s" % (pkg, pkg, f.name))
	provides = specParser.getProvidesFromPackageSections(f.name, pkg)
	f.close()
	return provides

def inverseMap(mfnc):
	"""inverse mapping of multifunction

	Keyword arguments:
	mfnc -- multifunction
	"""
	imap = {}
	for key in mfnc:
		for image in mfnc[key]:
			if image not in imap:
				imap[image] = [key]
			else:
				imap[image].append(key)
	return imap

def displayMapping(pkg, imap, fmt=False):
	if fmt:
		mlen = 0
		for arg in imap:
			mlen = max(mlen, len(arg))

		for arg in imap:
			print "%s%s -> %s" % (arg, " " * (mlen - len(arg)),  ",".join(imap[arg]))

	else:
		for arg in imap:
			print "%s:%s:%s" % (arg, pkg, ",".join(imap[arg]))

def loadPackages():
	packages = []
	with open("%s/golang.packages" % script_dir, "r") as file:
		for line in file.read().split('\n'):
			line = line.strip()
			if line == '':
				continue

			packages.append(line)
	return packages

if __name__ == "__main__":

	packages = loadPackages()
	for pkg in packages:
		provides = fetchProvides(pkg, 'master')
		imap = inverseMap(provides)
		displayMapping(pkg, imap)
		
