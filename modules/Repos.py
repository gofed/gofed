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
from Utils import runCommand
from Config import Config
import urllib
import json
import sys

repo_mappings = {}
###############################
# Import path to package name #
###############################
class IPMap:
	def loadIMap(self):
		imap = {}
		golang_imap_path = Config().getGolangIp2pkgMapping()
		try:
			with open(golang_imap_path, "r") as file:
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
		except IOError, e:
			sys.stderr.write("%s\n" % e)

		return imap

	def saveIMap(self, mapping):
		# golang(bitbucket.org/kardianos/osext):golang-bitbucket-kardianos-osext:golang-bitbucket-kardianos-osext-devel
		if mapping == []:
			return False

		golang_imap_path = Config().getGolangIp2pkgMapping()
		try:
			with open("%s.tmp" % golang_imap_path, "w") as file:
				sargs = sorted(mapping.keys())
				for arg in sargs:
					build, devel = mapping[arg]
					file.write("%s:%s:%s\n" % (arg, build, devel))
		except IOError, e:
			sys.stderr.write("%s\n" % e)
			return False

		return True

	def flush(self):
		golang_imap_path = Config().getGolangIp2pkgMapping()
		os.rename("%s.tmp" % golang_imap_path,
			golang_imap_path)

#################################################
# Internal database of packages and their repos #
#################################################
class Repos:

	def loadRepos(self):
		lines = []
		golang_repos_path = Config().getGolangRepos()
		try:
			with open(golang_repos_path, "r") as file:
				lines = file.read().split('\n')
		except IOError, e:
			sys.stderr.write("%s\n" % e)
			return {}

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

		golang_repos_path = Config().getGolangRepos()
		try:
			with open('%s.tmp' % golang_repos_path, "w") as file:
				spkgs = sorted(repos.keys())
				for pkg in spkgs:
					dir, git = repos[pkg]
					file.write("%s\t%s\t%s\n" % (pkg, dir, git))
		except IOError, e:
			sys.stderr.write("%s\n" % e)
			return False

		return True

	def flush(self):
		golang_repos_path = Config().getGolangRepos()
		os.rename("%s.tmp" % golang_repos_path,
			golang_repos_path)
	

	def parseReposInfo(self):
		# get path prefix
		path_prefix = Config().getRepoPathPrefix()

		lines = []
		golang_repos_path = Config().getGolangRepos()
		with open(golang_repos_path, "r") as file:
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

