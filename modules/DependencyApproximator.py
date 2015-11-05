from Base import Base
from GoSymbolsExtractor import GoSymbolsExtractor
from ImportPathsDecomposer import ImportPathsDecomposer
from ImportPath import ImportPath
from modules.Repos import Repos, getRepoCommits
import datetime
from SourceCodeStorage import SourceCodeStorage
from ProjectDecompositionGraphBuilder import ProjectDecompositionGraphBuilder
import sys
import copy

class CommitHandler(Base):
	"""
	For a given commit and project get its closes commit
	"""
	def __init__(self, commit, project):
		self.commit = commit
		self.project = project

class DependencyApproximator(Base):
	"""
	1) Provide a golang project and commit
	2) For the project get a list of its dependencies and determinate
	   the closest commit possible to the one provided (e.g. based on date)
	3) Decompose imported packages into classes
	4) For each class get a list of used packages (subset of project's packages)
	5) Mark import path prefix as of each processed class to avoid cycles
	6) For each new import path prefix found put it into a queue of projects to process (with a subset of packages to read)

	Here, I have a list of direct dependencies. Now get a list of indirect dependencies
	7) For each dependencies and a subset of its packages (in queue) construct a dependency graph of a project for given commit
	8) From each node in the dependency graph get a list of imported packages.
	9) For each list repeat step 2), 3), 4), 5) and 6)
	10) Repeat steps 7)-10) until the queue is empty

	There is a change to have two different commits for the same dependency (take the younger of them but report it to user)

	As dependencies are parsed only partially, cyclic dependencies can bring packages out of partially explored set.
	Thus dependencies are stored by package, not by prefix. This way it is assured all imported packages are processed.
	E.g A(1,2)->B(1), B(1)->C(2), C(2)->A(3). Here, packages 1 and 2 from A were imported first (and processed). Later on,
	package 3 from A was imported. As A was processed only partial, package 3 would not get processed normally. However as
	all imported packages are stored in queue, package 3 get processed eventually.

	"""
	def __init__(self, parser_config, commit_date, verbose=False):
		Base.__init__(self)
		self.err = []
		self.warn = []

		self.parser_config = parser_config
		self.import_path_prefix = self.parser_config.getImportPathPrefix()
		self.verbose = verbose
		self.pull = False

		self.local_repos = {}
		self.upstream_repo = {}
		self.commit_date = commit_date
		self.detected_commits = {}
		self.deps_queue = []
		self.defined_packages = {}

		self.source_code_storage = SourceCodeStorage("/var/lib/gofed/storage")

	def construct(self):
		self.getRepos()

		if self.verbose:
			sys.stderr.write("####Scanning direct dependencies####\n")

		self.getDirectDependencies()
		self.popDepsQueue()

		if self.verbose:
			sys.stderr.write("\n####Scanning indirect dependencies####\n")

		self.getIndirectDependencies()
		while self.deps_queue != []:
			self.getIndirectDependencies()

	def getDependencies(self):
		return self.detected_commits

	def getRepos(self):
		r_obj = Repos()
		repos = r_obj.parseReposInfo()
		self.local_repos = {}
		self.upstream_repo = {}

		# 'golang-github-boltdb-bolt': ('/var/lib/gofed/packages/golang-github-boltdb-bolt/upstream//bolt', 'https://github.com/boltdb/bolt.git')
		for name in repos:
			dir, repo = repos[name]

			m_repo = str.replace(repo, 'https://', '')
			m_repo = str.replace(m_repo, 'http://', '')

			if m_repo.endswith('.git'):
				m_repo = m_repo[:-4]

			if m_repo.endswith('.hg'):
				m_repo = m_repo[:-3]
	
			self.local_repos[m_repo] = dir
			self.upstream_repo[m_repo] = repo

	def popDepsQueue(self):
		# pop direct dependencies
		for dep in self.detected_commits:
			self.deps_queue.append(dep)

		# in case of cyclic deps let's pop project's packages as well
		#for pkg in self.defined_packages:
		#	self.deps_queue.append(pkg)

		return
		for ip in self.deps_queue:
			if ip in self.detected_commits:
				print "%s: %s" % (ip, self.detected_commits[ip]["Date"])
			else:
				print ip

	def detectProjectSubpackages(self, prefix, imported_packages):
		subpackages = []
		prefix_len = len(prefix)
		for ip in imported_packages:
			if ip.startswith(prefix):
				subpackage = ip[prefix_len:]
				if subpackage == "":
					subpackage = "."
				else:
					subpackage = subpackage[1:]
				subpackages.append( subpackage )
		return subpackages

	def processElement(self, element):
		# convert each import path prefix to provider prefix
		ip_obj = ImportPath(element)
		if not ip_obj.parse():
			self.err.append(ip_obj.getError())
			return {}

		provider_prefix = ip_obj.getProviderPrefix()
		if provider_prefix not in self.local_repos:
			self.err.append("Repository for %s not found" % provider_prefix)
			return {}

		#print self.local_repos[provider_prefix]
		path = self.local_repos[provider_prefix]
		upstream = self.upstream_repo[provider_prefix]

		# the list is not sorted by date
		commits = getRepoCommits(path, upstream, pull=self.pull)
		commit_dates = {}
		for commit in commits:
			commit_dates[ commits[commit] ] = commit

		last_commit_date = 1
		last_commit = -1
		for comm_date in sorted(commit_dates.keys()):
			#print (comm_date, self.commit_date)
			if int(comm_date) <= self.commit_date:
				last_commit_date = comm_date
				last_commit = commit_dates[comm_date]
			else:
				break

		str_date = datetime.datetime.fromtimestamp(int(last_commit_date)).strftime('%Y-%m-%d %H:%M:%S')

		info = {}
		info["Date"] = str_date
		info["Rev"] = last_commit
		info["ProviderPrefix"] = provider_prefix

		return info

	def getIndirectDependencies(self):
		"""
		All new deps put into local queue.
		Once deps_queue is done, replace it with local one.
		"""
		queue = []

		for ip in self.deps_queue:
			# for a fiven import path construct its partial graph
			parser_config = self.parser_config
			import_path_prefix = self.detected_commits[ip]["ImportPathPrefix"]
			parser_config.setImportPathPrefix( import_path_prefix )
			# set path to SourceCodeStorage
			path = self.source_code_storage.getDirectory(self.detected_commits[ip]["ProviderPrefix"], self.detected_commits[ip]["Rev"])
			parser_config.setParsePath(path)
			subpackages = self.detectProjectSubpackages(self.detected_commits[ip]["ImportPathPrefix"], [ip])
			# TODO(jchaloup): Later, add all packages of the same prefix to speed it up
			parser_config.setPartial(subpackages)

			if self.verbose:
				sys.stderr.write("Scanning %s: %s\n" % (self.detected_commits[ip]["ImportPathPrefix"], ",".join(subpackages)))

			gb = ProjectDecompositionGraphBuilder(parser_config)
			gb.buildFromDirectory(path)

			partial_deps = gb.getPartial()
			for ip_used in partial_deps:

				ipd = ImportPathsDecomposer(partial_deps[ip_used])
				if not ipd.decompose():
					self.err.append(ipd.getError())
					return False

				self.warn.append(ipd.getWarning())

				classes = ipd.getClasses()
				sorted_classes = sorted(classes.keys())

				for element in sorted_classes:
					if element == "Native":
						continue

					# class name starts with prefix => filter out
					if element.startswith(import_path_prefix):
						continue

					element_info = self.processElement(element)
					if element_info == {}:
						continue

					for ip in classes[element]:
						# is import path already checked in?
						if ip in self.detected_commits:
							#print "^^^^%s" % ip
							continue
						# TODO(jchaloup): or is ip in defined packages?

						info = copy.deepcopy(element_info)
						info["ImportPath"] = str(ip)
						info["ImportPathPrefix"] = element
						self.detected_commits[ip] = info
						if self.verbose:
							sys.stderr.write("%s\n" % str(info))

						queue.append(ip)

		self.deps_queue = queue
		return True

	def getDirectDependencies(self):

		gse_obj = GoSymbolsExtractor(self.parser_config)
		if not gse_obj.extract():
			self.err.append(gse_obj.getError())
			return False

		package_imports_occurence = gse_obj.getPackageImportsOccurences()

		ip_used = gse_obj.getImportedPackages()
		ipd = ImportPathsDecomposer(ip_used)
		if not ipd.decompose():
			self.err.append(ipd.getError())
			return False

		self.warn.append(ipd.getWarning())

		classes = ipd.getClasses()
		sorted_classes = sorted(classes.keys())

		for element in sorted_classes:
			if element == "Native":
				continue

			# class name starts with prefix => filter out
			if element.startswith(self.import_path_prefix):
				continue

			element_info = self.processElement(element)
			if element_info == {}:
				continue

			if self.verbose:
				sys.stderr.write(element + " (" + str(self.detectProjectSubpackages(element, classes[element])) + ")\n")

			for ip in classes[element]:
				info = copy.deepcopy(element_info)
				info["ImportPath"] = str(ip)
				info["ImportPathPrefix"] = element
				self.detected_commits[ip] = info
				if self.verbose:
					sys.stderr.write("%s\n" % str(info))

		for pkg in gse_obj.getSymbols().keys():
			ip, _ = pkg.split(":")
			if ip == ".":
				ip = self.import_path_prefix
			else:
				ip = "%s/%s" % (self.import_path_prefix, ip)
			self.defined_packages[ip] = {}

		return True
