# for a given project
# 1) read/get its dependencies (if there is no list, approximate one)
# 2) for each dependency get a pair (rawhide-commit, deps-commit)
# 3) for each pair get apidiff of its corresponding tarballs
# 4) for each dependency list items of apidiff (negative as default) and count them (to each change assign weight)
# 5) for the project print its deviation (sum of weighted numbers)

from DependencyFileParser import DependencyFileParser
from ImportPath import ImportPath
from Base import Base
from RemoteSpecParser import RemoteSpecParser
from SourceCodeStorage import SourceCodeStorage

class APIDeviation(Base):

	def __init__(self, project, verbose = False):
		# project's name (not package name)
		self.project = project
		self.verbose = verbose

	def compute(self):
		deps = self.readDeps()
		rawhide_commits = self.readPkgDBCommits(deps)
		self.getAPIDiff(deps, rawhide_commits)


	def importpath2pkgname(self, importpath):
		# TODO: maybe use some sort of cache of importpath -> packagename
		ip = ImportPath(importpath)
		if not ip.parse():
			return ""

		return ip.getPackageName()

	def readDeps(self):
		"""
		Get a list of dependencies
		"""
		deps_file = "/home/jchaloup/Packages/reviews/golang-heketi/Godeps.json"
        	dp = DependencyFileParser(deps_file)
        	return dp.parseGODEPSJSON()
		return {}

	def readPkgDBCommits(self, deps):
		"""
		For a list of depedencies, get corresponding commits from rawhide.
		1) Transform import path to package name
		2) For each package get its rawhide commit
		3) Get a list of rawhide commits for each dependency
		"""
		commits = {}
		for ip in deps:
			pkgname = self.importpath2pkgname(ip)
			rsp = RemoteSpecParser("master", pkgname)
			rawhide_commit = ""
			#if not rsp.parse():
			#	print "Unable to get commit for %s" % pkgname
			if self.verbose:
				print "Retrieving %s ..." % pkgname

			if rsp.parse():
				rawhide_commit = rsp.getPackageCommits()

			commits[ip] = rawhide_commit

		return commits

	def getAPIDiff(self, deps, commits):
		"""
		For each pair make apidiff(upstream, rawhide).
		Request for a directory containing tarballs in the form:
			provider-project-repo-commit
		"""

		scs = SourceCodeStorage("/tmp/test", self.verbose)
		if self.verbose:
			print "Collection tarballs..."

		print "Upstream\t\tRawhide"
		for ip in deps:
			if commits[ip] == "":
				continue

			print (ip, deps[ip], commits[ip])
			deps_dir = scs.getDirectory(ip, deps[ip])
			commits_dir = scs.getDirectory(ip, commits[ip])
			print (deps_dir, commits_dir)

		return {}
