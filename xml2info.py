#!/bin/python

import sys
from xml.dom import minidom
from xml.dom.minidom import Node
import optparse

ERR_NO_ERROR = 0
ERR_NO_BRANCHES = 1
ERR_NOT_BRANCH = 2
ERR_NOT_NAME_OR_BUILDS = 3
ERR_NOT_BUILD = 4
ERR_NOT_BUILD_TAGS = 5

def printErr(err):
	print "Error: %d" % err

def getLeafTagData(tag):
	for item in tag.childNodes:
		if item.nodeType == Node.TEXT_NODE:
			return item.data
	return ""

def inspectBuild(build):
	b_name = ""
	b_missing = []
	b_super = []
	b_exec = []
	clean = True
	for item in build.childNodes:
		if item.nodeType != Node.ELEMENT_NODE:
			continue

		if item.tagName == "name":
			b_name = getLeafTagData(item)
		elif item.tagName == "missing_provides":
			b_missing = getLeafTagData(item)
			if b_missing != "":
				b_missing = b_missing.split(',')
				clean = False
			else:
				b_missing = []
		elif item.tagName == "superfluous_provides":
			b_super = getLeafTagData(item)
			if b_super != "":
				b_super = b_super.split(',')
				clean = False
			else:
				b_super = []
		elif item.tagName == "executables":
			b_exec = getLeafTagData(item)
			if b_exec != "":
				b_exec = b_exec.split(',')
				clean = False
			else:
				b_exec = []

		else:
			return {}, ERR_NOT_BUILD_TAGS
	return {
		"name": b_name,
		"missing": b_missing,
		"super": b_super,
		"exec": b_exec,
		"clean": clean,
	}, ERR_NO_ERROR

def inspectBuilds(buildsElm):
	builds = []
	for build in buildsElm.childNodes:
		if build.nodeType != Node.ELEMENT_NODE:
			continue

		if build.tagName != "build":
			return [], ERR_NOT_BUILD
	
		b_info, err = inspectBuild(build)
		if err != ERR_NO_ERROR:
			printErr(err)
		else:
			builds.append(b_info)

	return builds

def inspectBranch(branch):
	b_name = ""
	b_builds = []

	if branch.tagName != "branch":
		return [], ERR_NOT_BRANCH

	for b_node in branch.childNodes:
		# <name> and <builds> tag
		if b_node.nodeType == Node.ELEMENT_NODE:
			if b_node.tagName == "name":
				for item in b_node.childNodes:
					if item.nodeType == Node.TEXT_NODE:
						b_name = item.data
			elif b_node.tagName == 'builds':
				b_builds = b_node
			else:
				return [], ERR_NOT_NAME_OR_BUILDS
	return {
		'name': b_name,
		'builds': inspectBuilds(b_builds)
	}, ERR_NO_ERROR

def showList(lst):
	for item in lst:
		print "\t" + item

def interpretScan(branches, short = True):
	for branch in branches:
		print 10*'=' + 'branch: ' + branch['name'] + 10*'='
		for build in branch['builds']:
			if short and build['clean']:
				continue

			print 'build: %s' % build['name']
			if build['exec']:
				print 'Executables:'
				showList(build['exec'])
			if build['super']:
				print 'Incorrect provides:'
				showList(build['super'])
			if build['missing']:
				print 'Missing provides:'
				showList(build['missing'])
		print ""

def sumarizeScan(branches):
	counter = {}
	for branch in branches:
		counter[branch['name']] = 0
		cnt = 0
		for build in branch['builds']:
			if build['clean']:
				continue

			if build['exec']:
				cnt = cnt + len(build['exec'])
			if build['super']:
				cnt = cnt + len(build['super'])
			if build['missing']:
				cnt = cnt + len(build['missing'])
		counter[branch['name']] = counter[branch['name']] + cnt

	return counter

def analyzeResults(branchesElm):
	branches = []
	for branchElm in branchesElm:
		if branchElm.nodeType == Node.ELEMENT_NODE:
			branch, err = inspectBranch(branchElm)
			if err != ERR_NO_ERROR:
				 printErr(err)
			else:
				branches.append(branch)
	return branches

if __name__ == "__main__":
	parser = optparse.OptionParser("%prog file")

        parser.add_option_group( optparse.OptionGroup(parser, "file", "Xml file with scanned results") )

	parser.add_option(
	    "", "-d", "--detail", dest="detail", action = "store_true", default = False,
	    help = "Display more information about affected branches"
	)

	options, args = parser.parse_args()

	if len(args) != 1:
		print "Usage: %s file.xml" % (sys.argv[0].split('/')[-1])
		exit(0)

	xmlfile = args[0]
	xmldoc = minidom.parse(xmlfile)

	brchs_elm = xmldoc.getElementsByTagName('branches')
	if len(brchs_elm) == 0:
		exit(ERR_NO_BRANCHES)

	pkg_name = getLeafTagData(xmldoc.getElementsByTagName('name')[0])
	branches = analyzeResults(brchs_elm[0].childNodes)

	if options.detail:
		interpretScan(branches)
	else:
		summary = sumarizeScan(branches)
		info = []
		for br in summary:
			info.append(br + " (%d)" % summary[br])

		print "%s: %s" % (pkg_name, ', '.join(info))

	exit(0)
