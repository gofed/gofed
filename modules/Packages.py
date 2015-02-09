#!/bin/python
from subprocess import Popen, PIPE
from Utils import getScriptDir
from Utils import runCommand
import re
import os
import tempfile
import shutil
from Repos import detectRepoPrefix

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
		#self.initTempDir()
		cwd = os.getcwd()
		self.tmp_dir = '/tmp/tmpGwWwL9'
		os.chdir(self.tmp_dir)
		#self.downloadBuilds()
		print self.analyzeBuilds()
		os.chdir(cwd)
		#self.clearTempDir()

	def getLatestBuilds(self, tag = 'rawhide'):
		so, _, rc = runCommand("koji -q latest-build %s %s" % (tag, self.pkg_name))
		if rc != 0:
			return ''
		return re.sub(r'[ \t]+', ' ', so.strip()).split(' ')[0]

	def downloadBuilds(self, tag = 'rawhide'):
		"""
		Download all builds in the currect directory
		"""
		build = self.getLatestBuilds(tag)
		if build == "":
			return False

		so, se, rc = runCommand("koji download-build %s" % build)
		if rc != 0:
			return False

		return True

	def analyzeDevelBuild(self, name):
		"""
		Expects build in the current directory
		"""

		_, _, rc = runCommand("mkdir -p build")
		if rc != 0:
			return {}

		os.chdir('build')
		runCommand('rm -rf *')
		runCommand('rpm2cpio ../%s | cpio -idmv' % name)

		build_prefix = []
		build_provides = []
		build_import_paths = []

		# get all possible provided import paths
		so, se, _ = runCommand("go2fed inspect -p")
		for line in so.split('\n'):
			line = line.strip()

			if line == '':
				continue
			
			if line.startswith('usr/share/gocode/src/'):
				line = line[21:]
				prefix = detectRepoPrefix(line)
				if prefix not in build_prefix:
					build_prefix.append(prefix)
				build_provides.append(line)
			else:
				os.chdir('..')
				return {}

		so, se, _ = runCommand("go2fed ggi")
		for line in so.split('\n'):
			line = line.strip()

			if line == '':
				continue

			for prefix in build_prefix:
				if not line.startswith(prefix):
					build_import_paths.append(line)
		os.chdir('..')

		return {
			"provides": build_provides,
			"imports":  build_import_paths
			}
	
	def analyzeBuilds(self):
		"""
		For each build return its import paths and provides,
		which are computed from source codes, not from quering a build.
		"""

		builds = {}

		so, _, _ = runCommand("ls")
		
		for line in so.split('\n'):
			line = line.strip()

			if line == '':
				continue

			# from N-V-R get name
			parts = line.split('-')

			if len(parts) < 3:
				continue

			name = "-".join(parts[:-2])

			if name.endswith('devel'):
				info = self.analyzeDevelBuild(line)
				if info != {}:
					builds[name] = info

		return builds

	def initTempDir(self):
		self.tmp_dir = tempfile.mkdtemp()
		
	def clearTempDir(self):
		shutil.rmtree(self.tmp_dir)

	#def extr
	#	so, se, rc = runCommand("koji download-build %s" % build)


if __name__ == "__main__":
	pkg = Package('golang-googlecode-net')
