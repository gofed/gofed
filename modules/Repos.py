# -*- coding: utf-8 -*-
#############################################################################
# File          : Repos.py
# Package       : gofed
# Author        : Jan Chaloupka
# Created on    : Sat Jan  17 11:08:14 2014
# Purpose       : ---check the spec file of a source rpm.
#############################################################################
import re
import os
from Utils import getScriptDir
from Utils import runCommand
from Config import Config
import urllib
import json

script_dir = getScriptDir() + "/.."
repo_mappings = {}
GOLANG_IMAP="data/golang.imap"
GOLANG_REPOS="data/golang.repos"
###############################
# Import path to package name #
###############################
class IPMap:
	def loadIMap(self):
		imap = {}
		with open("%s/%s" % (script_dir, GOLANG_IMAP), "r") as file:
			for line in file.read().split('\n'):
				line = line.strip()
				if line == '':
					continue

				parts = line.split(":")
				if len(parts) != 3:
					continue

				parts[0] = parts[0].strip()
				if parts[0] not in imap:
					imap[parts[0]] = (parts[1], parts[2])
		return imap

	def saveIMap(self, mapping):
		# golang(bitbucket.org/kardianos/osext):golang-bitbucket-kardianos-osext:golang-bitbucket-kardianos-osext-devel
		if mapping == []:
			return False

		with open("%s/%s.tmp" % (script_dir, GOLANG_IMAP), "w") as file:
			sargs = sorted(mapping.keys())
			for arg in sargs:
				build, devel = mapping[arg]
				file.write("%s:%s:%s\n" % (arg, build, devel))

		return True

	def flush(self):
		os.rename("%s/%s.tmp" % (script_dir, GOLANG_IMAP),
			"%s/%s" % (script_dir, GOLANG_IMAP))

#################################################
# Internal database of packages and their repos #
#################################################
class Repos:

	def loadRepos(self):
		lines = []
		with open('%s/%s' % (script_dir, GOLANG_REPOS), "r") as file:
			lines = file.read().split('\n')

		repos = {}
		for line in lines:
			line = line.strip()
			if line == '' or line[0] == '#':
				continue

			line = re.sub(r'[ \t]+', ' ', line)
			line = line.split(' ')

			if len(line) != 3:
				continue

			line[0] = line[0].strip()
			line[1] = line[1].strip()
			line[2] = line[2].strip()

			# pkg_name, path_to_repo, upstream repo
			repos[line[0]] = (line[1], line[2])

		return repos

	def saveRepos(self, repos):
		if repos == []:
			return False

		with open('%s/%s.tmp' % (script_dir, GOLANG_REPOS), "w") as file:
			spkgs = sorted(repos.keys())
			for pkg in spkgs:
				dir, git = repos[pkg]
				file.write("%s\t%s\t%s\n" % (pkg, dir, git))

		return True

	def flush(self):
		os.rename("%s/%s.tmp" % (script_dir, GOLANG_REPOS),
			"%s/%s" % (script_dir, GOLANG_REPOS))
	

	def parseReposInfo(self):
		# get path prefix
		path_prefix = Config().getRepoPathPrefix()

		lines = []
		with open('%s/%s' % (script_dir, GOLANG_REPOS), "r") as file:
			lines = file.read().split('\n')

		repos = {}
		for line in lines:
			line = line.strip()
			if line == '' or line[0] == '#':
				continue

			line = re.sub(r'[ \t]+', ' ', line)
			line = line.split(' ')

			if len(line) != 3:
				continue

			line[0] = line[0].strip()
			line[1] = line[1].strip()
			line[2] = line[2].strip()

			# pkg_name, path_to_repo, upstream repo
			prefix = ''
			if path_prefix != '':
				# does prefix_path contains %pkg?
				prefix = re.sub(r'%pkg', line[0], path_prefix)

			if line[1][0] != '/':
				if prefix == '':
					print "Error: %s repo path must be absolute path. Perhaps set repo_path_prefix." % line[0]
					return {}
				else:
					line[1] = prefix + "/" + line[1]

			repos[line[0]] = (line[1], line[2])

		return repos

def getRepoCommits(path, repo, pull=True):

	# path does not exists? create one
	runCommand("mkdir -p %s" % path)
	cwd = os.getcwd()
	os.chdir('/'.join(path.split('/')[:-1]))

	logs = ""
	# git or hg?
	if len(repo) < 4 or repo[-4:] != '.git':
		runCommand("hg clone %s" % repo)
		repo_dir = repo.split('/')[-1]
		os.chdir(repo_dir)

		if pull:
			runCommand("hg pull")

		logs, se, rc = runCommand('hg log --template "{date|hgdate} {node}\n" | cut -d" " -f1,3 | sed "s/ /:/g"')
	else:
		runCommand("git clone %s" % repo)
		repo_dir = repo.split('/')[-1][:-4]
		os.chdir(repo_dir)

		if pull:
			runCommand('git pull')

		logs, se, rc = runCommand('git log --pretty=format:"%ct:%H"')

	commits = {}
	for line in logs.split('\n'):
		line = line.strip().split(':')

		if len(line) != 2:
			continue

		# timestamp:commit
		commits[ line[1] ] = line[0]

	os.chdir(cwd)
	return commits

#################################################
# github.com, bitbucket.org auxiliary functions #
#################################################
def getGithubLatestCommit(project, repo):
	link = "https://api.github.com/repos/%s/%s/commits" % (project, repo)
	f = urllib.urlopen(link)
	c_file = f.read()
	# get the latest commit
	commits = json.loads(c_file)
	if type(commits) != type([]):
		return ""

	if len(commits) == 0:
		return ""

	if "sha" not in commits[0]:
		return ""

	return commits[0]["sha"]

def getBitbucketLatestCommit(project, repo):
	link = "https://bitbucket.org/api/1.0/repositories/%s/%s/changesets?limit=1" % (project, repo)
	f = urllib.urlopen(link)
	c_file = f.read()
	# get the latest commit
	data = json.loads(c_file)
	if 'changesets' not in data:
		return ""

	commits = data['changesets']
	if type(commits) != type([]):
		return ""

	if len(commits) == 0:
		return ""

	if 'raw_node' not in commits[0]:
		return ""

	return commits[0]["raw_node"]

