# -*- coding: utf-8 -*-
#############################################################################
# File          : Repos.py
# Package       : go2fed
# Author        : Jan Chaloupka
# Created on    : Sat Jan  17 11:08:14 2014
# Purpose       : ---check the spec file of a source rpm.
#############################################################################
import re
import os
import Utils

script_dir = Utils.getScriptDir()
GOLANG_IMAP="golang.imap"
GOLANG_REPOS="golang.repos"

#####################
# Detect known repo #
#####################
UNKNOWN = 0
GITHUB = 1
GOOGLECODE = 2
GOLANGORG = 3
GOPKG = 4

def detectKnownRepos(url):
	url = re.sub(r'http://', '', url)
	url = re.sub(r'https://', '', url)

	if url.startswith('github.com'):
		return GITHUB, url
	if url.startswith('code.google.com/p'):
		return GOOGLECODE, url
	if url.startswith('golang.org/x'):
		return GOLANGORG, url
	if url.startswith('gopkg.in'):
		return GOPKG, url

	return UNKNOWN, ''

##########################################################
# For given import path, detect its repo specific prefix #
##########################################################
# only github.com/<project>/<repo> denote a class
def detectGithub(path):
	parts = path.split('/')
	return '/'.join(parts[:3])

# only code.google.com/p/<repo>
def detectGooglecode(path):
	parts = path.split('/')
        return '/'.join(parts[:3])

# only golang.org/x/<repo>
def detectGolangorg(path):
	parts = path.split('/')
        return '/'.join(parts[:3])

# only gopkg.in/<v>/<repo>
# or   gopkg.in/<repo>.<v>
def detectGopkg(path):
	parts = path.split('/')
	if re.match('v[0-9]+', parts[1]) and len(parts) >= 3:
		return '/'.join(parts[:3])
	else:
		return '/'.join(parts[:2])

###################################################
# Transformation of repo name to its package name #
###################################################
def github2pkgdb(github):
	# github.com/<project>/<repo>
	parts = github.split('/')
	if len(parts) == 3:
		return "golang-github-%s-%s" % (parts[1], parts[2])
	else:
		return ""

def googlecode2pkgdb(googlecode):
	# code.google.com/p/<repo>
	parts = googlecode.split('/')
        if len(parts) == 3:
		# rotate the repo name
		nparts = parts[2].split('.')
		if len(nparts) > 2:
			print "%s repo contains more than one dot in its name, not implemented" % '/'.join(parts[:3])
			exit(1)
		if len(nparts) == 2:
			return "golang-googlecode-%s" % (nparts[1] + "-" + nparts[0])
		else:
			return "golang-googlecode-%s" % parts[2]
        else:
                return ""

def golangorg2pkgdb(github):
	# golang.org/x/<repo>
	parts = github.split('/')
	parts[0] = 'code.google.com'
	parts[1] = 'p'
	return googlecode2pkgdb('/'.join(parts))

###############################
# Import path to package name #
###############################
def loadIMap():
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

#################################################
# Internal database of packages and their repos #
#################################################
def parseReposInfo():
	# get path prefix
	path_prefix = ''
	with open('%s/%s' % (script_dir, 'config/go2fed.conf'), 'r') as file:
		lines = file.read().split('\n')
		for line in lines:
			if line == '' or line[0] == '#':
				continue

			line = line.strip()

			if line.startswith('repo_path_prefix'):
				line = re.sub(r'[ \t]+', ' ', line)
				parts = line.split(' ')
				if len(parts) != 2:
					print "Warning: invalid repo_path_prefix"
					return {}
				path_prefix = parts[1]
				break

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
	Utils.runCommand("mkdir -p %s" % path)
	cwd = os.getcwd()
	os.chdir('/'.join(path.split('/')[:-1]))

	logs = ""
	# git or hg?
	if len(repo) < 4 or repo[-4:] != '.git':
		Utils.runCommand("hg clone %s" % repo)
		repo_dir = repo.split('/')[-1]
		os.chdir(repo_dir)

		if pull:
			Utils.runCommand("hg pull")

		logs, se, rc = Utils.runCommand('hg log --template "{date|hgdate} {node}\n" | cut -d" " -f1,3 | sed "s/ /:/g"')
	else:
		Utils.runCommand("git clone %s" % repo)
		repo_dir = repo.split('/')[-1][:-4]
		os.chdir(repo_dir)

		if pull:
			Utils.runCommand('git pull')

		logs, se, rc = Utils.runCommand('git log --pretty=format:"%ct:%H"')

	commits = {}
	for line in logs.split('\n'):
		line = line.strip().split(':')

		if len(line) != 2:
			continue

		# timestamp:commit
		commits[ line[1] ] = line[0]

	os.chdir(cwd)
	return commits


if __name__ == '__main__':
	# test detectGithub
	value = detectGithub('github.com/emicklei/go-restful/swagger')
	if value != 'github.com/emicklei/go-restful':
		print 'detectGithub Failed'
	else:
		print 'detectGithub Passed'

	# test detectGooiglecode
	value = detectGooglecode('code.google.com/p/google-api-go-client/googleapi/internal/uritemplates')
	if value != 'code.google.com/p/google-api-go-client':
		print 'detectGooglecode Failed'
	else:
		print 'detectGooglecode Passed'

	# test detectGolangorg
	value = detectGolangorg('golang.org/x/text/collate/colltab')
	if value != 'golang.org/x/text':
		print 'detectGolangorg Failed'
	else:
		print 'detectGolangorg Passed'

