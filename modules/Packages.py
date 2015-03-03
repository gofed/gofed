#!/bin/python
from Utils import getScriptDir, runCommand, inverseMap
import re
import os
import tempfile
import shutil
from Repos import detectRepoPrefix
from ImportPaths import loadImportPathDb
import operator
from GoSymbols import ProjectToXml
from specParser import getPkgURL, fetchProvides
from Repos import Repos, IPMap

GOLANG_PACKAGES="data/golang.packages"
GOLANG_PKG_DB="data/pkgdb"
script_dir = getScriptDir() + "/.."

def loadPackages():
	packages = []
	with open("%s/%s" % (script_dir, GOLANG_PACKAGES), "r") as file:
		for line in file.read().split('\n'):
			line = line.strip()
			if line == '' or line[0] == '#':
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
		self.latest_build = ""
		self.initTempDir()
		cwd = os.getcwd()
		os.chdir(self.tmp_dir)
		self.downloadBuilds()
		self.info = self.analyzeBuilds()
		os.chdir(cwd)
		self.clearTempDir()

	def getLatestBuilds(self, tag = 'rawhide'):
		so, _, rc = runCommand("koji -q latest-build %s %s" % (tag, self.pkg_name))
		if rc != 0:
			return ''
		return re.sub(r'[ \t]+', ' ', so.strip()).split(' ')[0]

	def downloadBuilds(self, tag = 'rawhide'):
		"""
		Download all builds in the currect directory
		"""
		self.latest_build = self.getLatestBuilds(tag)
		if self.latest_build == "":
			return False

		so, se, rc = runCommand("koji download-build %s" % self.latest_build)
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

		package_xml = ProjectToXml("", "%s/%s" % (os.getcwd(), 'usr/share/gocode/src/'), self.latest_build)

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
			"imports":  build_import_paths,
			"xmlobj": package_xml
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

	def getInfo(self):
		return self.info

def savePackageInfo(pkg_info):
	errs = []
	for build in pkg_info:
		obj = pkg_info[build]["xmlobj"]
		if not obj.getStatus():
			errs.append("Warning: unable to parse %s. Error: %s" % (build, obj.getError()))
			continue

		with open("%s/%s/%s.xml" % (script_dir, GOLANG_PKG_DB, build), "w") as f:
			f.write(str(obj))

	return errs

def getPackagesFromPkgDb():
	so, _, rc = runCommand("koji search --regex package '^golang-'")
	if rc != 0:
		return []

	pkgs = []

	for line in so.split('\n'):
		line = line.strip()

		if line == "":
			continue

		line = line.strip()
		pkgs.append(line)

	return pkgs

# based on http://www.fit.vutbr.cz/study/courses/GAL/public/gal-slides.pdf
def transposeGraph(graph):
	nodes, edges = graph
	tedges = {}
	for u in edges:
		for v in edges[u]:
			# (u,v) -> (v,u)
			if v not in tedges:
				tedges[v] = [u]
			else:
				tedges[v].append(u)

	return (nodes, tedges)

class DFS:

	def __init__(self, graph):
		self.nodes, self.edges = graph

		self.WHITE=0
		self.GRAY=1
		self.BLACK=2

		self.color = {}
		self.d = {}
		self.f = {}
		self.time = 0
		self.pred = {}



	def DFSVisit(self, node):
		self.color[node] = self.GRAY
		self.time += 1
		self.d[node] = self.time

		if node in self.edges:
			for adj in self.edges[node]:
				if self.color[adj] == self.WHITE:
					self.pred[adj] = node
					self.DFSVisit(adj)

		self.color[node] = self.BLACK
		self.time += 1
		self.f[node] = self.time

	def DFSWalk(self, f = []):
		for node in self.nodes:
			self.color[node] = self.WHITE
			self.pred[node] = ""

		self.time = 0

		if f == []:
			for node in self.nodes:
				if self.color[node] == self.WHITE:
					self.DFSVisit(node)
			return (self.f, self.d)
		else:
			start_nodes = []
			for node, _ in sorted(f.items(), key=operator.itemgetter(1), reverse=True):
				if self.color[node] == self.WHITE:
					self.DFSVisit(node)
				start_nodes.append(node)

			return (start_nodes, self.pred)

def getSucc(s, pred):
	if pred[s] == '':
		return [s]
	else:
		return [s] + getSucc(pred[s], pred)

def getSCC(graph):
	nodes, edges = graph
	f, d = DFS(graph).DFSWalk()
	tgraph = transposeGraph(graph)
	start_nodes, pred = DFS(tgraph).DFSWalk(f)
	trees = []
	for node in start_nodes:
		trees.append(getSucc(node, pred))

	# some trees can overlap
	scc = []
	for i_tree in trees:
		iss = False
		for j_tree in trees:
			if i_tree == j_tree:
				continue
			if set(i_tree).issubset(j_tree):
				iss = True
		if iss == False:
			scc.append(i_tree)

	return scc

def buildRequirementGraph(verbose=False):
	# load imported and provided paths
	ip_provides, ip_imports, pkg_devel_main_pkg = loadImportPathDb()
	# 1) for each package get a list of all packages it needs
	# 2) in this list find all cyclic dependencies

	# create mapping of import paths of provides to pkg_devel_name
	provides_mapping = {}
	pkgs = []
	for pkg_devel in ip_provides:
		pkgs.append(pkg_devel)
		for ip in ip_provides[pkg_devel]:
			if ip == "":
				continue

			provides_mapping[ip] = pkg_devel



	#print provides_mapping
	#pkgs = list(set(pkgs))
	#for line in sorted(pkgs):
	#	print line

	# Assuming all dependencies will create a sparse matrix, lets use a list of edges instead
	# (u, v) \in Pkgs \times Pkgs \eq u [B]R v (u needs v)
	edges = {}
	for pkg_devel in ip_imports:
		for ip in ip_imports[pkg_devel]:
			if ip == "":
				continue

			if ip not in provides_mapping:
				if verbose:
					print "Error: %s path of %s subpackage is not provided by any package" % (ip, pkg_devel)
				continue

			if pkg_devel not in edges:
				edges[pkg_devel] = [provides_mapping[ip]]
			else:
				if provides_mapping[ip] not in edges[pkg_devel]:
					edges[pkg_devel].append(provides_mapping[ip])

	return (pkgs, edges)

def getLeafPackages(graph):
	nodes, edges = graph

	leaves = []

	for u in nodes:
		if u not in edges:
			leaves.append(u)

	return leaves

def getRootPackages(graph):
	nodes, edges = graph

	roots = []

	visited = {}
	for u in nodes:
		visited[u] = 0

	for u in nodes:
		if u in edges:
			for v in edges[u]:
				visited[v] = 1

	for u in nodes:
		if visited[u] == 0:
			roots.append(u)

	return roots


class LocalDB:
	def loadPackages(self):
		packages = []
		with open("%s/%s" % (script_dir, GOLANG_PACKAGES), "r") as file:
			for line in file.read().split('\n'):
				line = line.strip()
				if line == '' or line[0] == '#':
					continue

				if line not in packages:
					packages.append(line)
		return packages

	def savePackages(self, packages):
		if packages == []:
			return False

		with open("%s/%s.tmp" % (script_dir, GOLANG_PACKAGES), "w") as file:
			for pkg in packages:
				file.write("%s\n" % pkg)	

		return True

	def flush(self):
		os.rename("%s/%s.tmp" % (script_dir, GOLANG_PACKAGES),
			"%s/%s" % (script_dir, GOLANG_PACKAGES))

	# 1) get a list of new packages
	# 2) add the list into golang.packages
	# 3) update golang.repos (detect import path from import_path macro)
	# 4) update golang.imap for mapping of import paths into their builds (devel packages)
	# 5) regenerate golang.importdb (or remove it and use pkg?)
	# -- if possible, regenerate only a part of golang.importdb/pkg only for new packages
	def addPackages(self, new_packages):
		err = []

		if new_packages == []:
			err.append("No new packages to add")
			return err, False

		# update golang.repos
		new_repos = {}

		checked_packages = []
		for pkg in new_packages:
			url = getPkgURL(pkg)
			if url == "":
				err.append("Unable to get URL tag from %s's spec file" % pkg)	
				continue
			checked_packages.append(pkg)
			# BUILD   go-spew https://github.com/davecgh/go-spew.git
			dir = os.path.basename(url)
			git = ("%s.git" % url)
			new_repos[pkg] = (dir, git)

		new_packages = checked_packages

		# get current packages
		curr_pkgs = self.loadPackages()
		for pkg in new_packages:
			curr_pkgs.append(pkg)

		# add new packages
		if not self.savePackages(sorted(curr_pkgs)):
			err.append("Unable to save new packages")
			return err, False


		repos = Repos().loadRepos()
		for repo in new_repos:
			repos[repo] = new_repos[repo]

		if not Repos().saveRepos(repos):
			err.append("Unable to save new repositories")
			return err, False

		# update import paths
		mapping = IPMap().loadIMap()

		for pkg in new_packages:
			provides = fetchProvides(pkg, 'master')
			imap = inverseMap(provides)
			for arg in imap:
				for image in imap[arg]:
					mapping[arg] = (pkg, image)

		if not IPMap().saveIMap(mapping):
			err.append("Unable to save mapping of import paths of new packages")
			return err, False

		self.flush()
		Repos().flush()
		IPMap().flush()
		return err, True

if __name__ == "__main__":
	#pkg = Package('golang-googlecode-net')
	#print pkg.getInfo()
	getPackagesFromPkgDb()
