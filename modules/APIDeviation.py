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
from GoSymbols import CompareSourceCodes
from Config import Config
from Utils import RED, ENDC, BLUE
import json

class APIDeviation(Base):

	def __init__(self, project, depsfile, verbose = False):
		# project's name (not package name)
		self.project = project
		self.verbose = verbose
		self.depsfile = depsfile
		self.apidiff = {}

	def compute(self):
		deps = self.readDeps()
		rawhide_commits = self.readPkgDBCommits(deps)
		return self.getAPIDiff(deps, rawhide_commits)

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
        	dp = DependencyFileParser(self.depsfile)
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

			# cache
			#json_deps = []
			#with open("/tmp/test/cache.json", 'r') as file:
			#	json_deps = json.loads(file.read())

			#if ip in json_deps:
			#	commits[ip] = json_deps[ip]
			#	continue

			rsp = RemoteSpecParser("master", pkgname)
			rawhide_commit = ""
			#if not rsp.parse():
			#	print "Unable to get commit for %s" % pkgname
			if self.verbose:
				print "Retrieving %s ..." % pkgname

			if rsp.parse():
				rawhide_commit = rsp.getPackageCommits()

			print "\"%s\": \"%s\"," % (ip, rawhide_commit)
			commits[ip] = rawhide_commit

		return commits

	def getDiff(self):
		return self.apidiff

	def getAPIDiff(self, deps, commits):
		"""
		For each pair make apidiff(upstream, rawhide).
		Request for a directory containing tarballs in the form:
			provider-project-repo-commit
		"""

		scs = SourceCodeStorage("/var/lib/gofed/storage", self.verbose)
		if self.verbose:
			print "Collection tarballs..."

		noGodeps = Config().getSkippedDirectories()

		self.apidiff = {}

		print "Upstream\t\tRawhide"
		for ip in deps:
			if commits[ip] == "":
				continue

			self.apidiff[ip] = {'rawhide': commits[ip], 'upstream': deps[ip], 'diff': []}

			deps_dir = scs.getDirectory(ip, deps[ip])
			commits_dir = scs.getDirectory(ip, commits[ip])
			#print (deps_dir, commits_dir)
			config = ParserConfig()
			if options.skiperrors:
				config.setSkipErrors()
			config.setNoGodeps(noGodeps)

			cmp_src = CompareSourceCodes(config)
			#print "Comparing"
			print "Processing %s ..." % ip
			cmp_src.compareDirs(deps_dir, commits_dir)

			for e in cmp_src.getError():
				print "Error: %s" % e

			apichanges = cmp_src.getStatus()

			for pkg in apichanges:
				if pkg == "+":
					continue

				if pkg == "-":
					self.apidiff[ip]['diff'].append({'package': '', 'change': apichanges[pkg]})
					continue

				#print "%sPackage: %s%s" % (BLUE, pkg, ENDC)
				for change in apichanges[pkg]:
					if change[0] == '-':
						self.apidiff[ip]['diff'].append({'package': pkg, 'change': change})

		return True

		for ip in deps:
			if ip not in apidiff:
				continue

			print "%s: |%s - %s|" % (ip, apidiff[ip]['upstream'], apidiff[ip]['rawhide'])
			for change in apidiff[ip]['diff']:
				print "\t%s%s%s" % (RED, change, ENDC)

			# TODO:
			# - output all deps without any rawhide commits as well (smth like NOT FOUND)
			# - cound the deviation

		return True
