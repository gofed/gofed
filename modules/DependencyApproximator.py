from Base import Base
from GoSymbolsExtractor import GoSymbolsExtractor
from ImportPathsDecomposer import ImportPathsDecomposer
from ImportPath import ImportPath
from modules.Repos import Repos, getRepoCommits
import datetime

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

	"""
	def __init__(self, parser_config, commit_date):
		Base.__init__(self)
		self.err = []

		self.parser_config = parser_config
		self.import_path_prefix = self.parser_config.getImportPathPrefix()
		self.pull = False

		self.local_repos = {}
		self.upstream_repo = {}
		self.commit_date = commit_date
		self.detected_commits = {}
		self.deps_queue = []
		self.defined_packages = {}

	def construct(self):
		self.getRepos()
		self.getDirectDependencies()
		self.popDepsQueue()

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
		for pkg in self.defined_packages:
			self.deps_queue.append(pkg)

		for ip in self.deps_queue:
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

		self.warn = ipd.getWarning()

		classes = ipd.getClasses()
		sorted_classes = sorted(classes.keys())

		for element in sorted_classes:
			if element == "Native":
				continue

			# class name starts with prefix => filter out
			if element.startswith(self.import_path_prefix):
				continue

			# convert each import path prefix to provider prefix
			ip_obj = ImportPath(element)
			if not ip_obj.parse():
				self.err.append(ip_obj.getError())
				continue

			provider_prefix = ip_obj.getProviderPrefix()
			if provider_prefix not in self.local_repos:
				self.err.append("Repository for %s not found" % provider_prefix)
				continue

			#print self.local_repos[provider_prefix]
			path = self.local_repos[provider_prefix]
			upstream = self.upstream_repo[provider_prefix]

			commits = getRepoCommits(path, upstream, pull=self.pull)
			last_commit_date = 1
			last_commit = -1
			for commit in commits:
				if commits[commit] <= self.commit_date:
					last_commit_date = commits[commit]
					last_commit = commit
				else:
					break

			str_date = datetime.datetime.fromtimestamp(int(last_commit_date)).strftime('%Y-%m-%d %H:%M:%S')

			print element + " (" + str(self.detectProjectSubpackages(element, classes[element])) + ")"
			for ip in classes[element]:
				info = {}
				info["ImportPath"] = str(ip)
				info["Comment"] = str_date
				info["Rev"] = last_commit
				self.detected_commits[ip] = info

		for pkg in gse_obj.getSymbols().keys():
			ip, _ = pkg.split(":")
			if ip == ".":
				ip = self.import_path_prefix
			else:
				ip = "%s/%s" % (self.import_path_prefix, ip)
			self.defined_packages[ip] = {}

		return True
