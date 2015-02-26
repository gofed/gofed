#!/bin/python

###############################################################################
# ========exported symbols (package units)========
# 1) list all directories containing go files
# 2) for each file in each directory list all its symbols
# 3) merge symbols belonging to the same package
# 4) for each import path make a database of all symbols
# 5) create go2fed gosymbols script (--list, --importpath, --status)
#
# ========imported symbols (file units)========
# 1) for each file list all imports
# 2) for each file search for all used types, variables, constants, functions
# 3) 
#
# - if . imports are presented, it is not trivial to know from which package
# used symbols are imported. What I have to do is to:
#   a) check the package for all defined local functions, variables, constants
#      and types
#   b) from each . import, list all symbols. If symbols are not mutually
#      exclusive (this can change by any package  update), report error.
#   c) from each file list all symbols not found in a)
#   d) map symbols found in c) to symbols exported from all . imports
#
# Each day make a snapshot of all provided import paths and exported symbols.
# This will be used as a source for "used symbols" matching
#
###############################################################################
# Using GoSymbols scan will replace go2fed scan-imports as it has a list of all
# packages and all imports. Exported symbols gives more informations about what
# is provided. Local database format has to be replaced with a more expressive
# one. Using xml for that as it can be read as it is.
#
# Extracted json should be transformed into a better representation (some keys
# are redundant, some types can be described in a more simple way.
###############################################################################

import os
from Utils import runCommand, getScriptDir
import json

def getGoDirs(directory, test = False):
	go_dirs = []
	for dirName, subdirList, fileList in os.walk(directory):
		# does the dirName contains *.go files
		nogo = True
		for fname in fileList:
			# find any *.go file
			if test == False and fname.endswith(".go"):
				nogo = False
				break
			elif test == True and fname.endswith("_test.go"):
				nogo = False
				break

		if nogo:
			continue

		relative_path = os.path.relpath(dirName, directory)
		go_dirs.append(relative_path)

	return go_dirs	

def getGoFiles(directory):
	go_dirs = []
	for dirName, subdirList, fileList in os.walk(directory):
		# skip all directories with no file
		if fileList == []:
			continue

		go_files = []
		for fname in fileList:
			# find any *.go file
			# but skip all test files
			if fname.endswith("_test.go"):
				continue

			if fname.endswith(".go"):
				go_files.append(fname)

		# skipp all directories with no *.go file
		if go_files == []:
			continue

		relative_path = os.path.relpath(dirName, directory)
		go_dirs.append({
			'dir': relative_path,
			'files': go_files
		})

	return go_dirs

def getGoSymbols(path):
	script_dir = getScriptDir() + "/.."
	so, se, rc = runCommand("%s/parseGo %s" % (script_dir, path))
	if rc != 0:
		return (1, se)

	return (0, so)



def mergeGoSymbols(jsons = []):
	"""
	Exported symbols for a given package does not have any prefix.
	So I can drop all import paths that are file specific and merge
	all symbols.
	Assuming all files in the given package has mutual exclusive symbols.
	"""
	# <siXy> imports are per file, exports are per package
	# on the highest level we have: pkgname, types, funcs, vars, imports.

	symbols = {}
	symbols["types"] = []
	symbols["funcs"] = []
	symbols["vars"]  = []
	for file_json in jsons:
		symbols["types"] += file_json["types"]
		symbols["funcs"] += file_json["funcs"]
		symbols["vars"]  += file_json["vars"]

	return symbols

def getSymbolsForImportPaths(go_dir):
	bname = os.path.basename(go_dir)
	go_packages = {}
	ip_packages = {}
	for dir_info in getGoFiles(go_dir):
		#if sufix == ".":
		#	sufix = bname
		pkg_name = ""
		jsons = {}
		for go_file in dir_info['files']:
			go_file_json = {}
			err, output = getGoSymbols("%s/%s/%s" % 
				(go_dir, dir_info['dir'], go_file))
			if err != 0:
				return "Error parsing %s: %s" % ("%s/%s" % (dir_info['dir'], go_file), output), {}, {}
			else:
				#print go_file
				go_file_json = json.loads(output)

			if pkg_name != "" and pkg_name != go_file_json["pkgname"]:
				return "Error: directory %s contains defines of more packages, i.e. %s" % (dir_info['dir'], pkg_name), {}, {}

			pkg_name = go_file_json["pkgname"]
			# skip all main packages
			if pkg_name == "main":
				continue

			if pkg_name not in jsons:
				jsons[pkg_name] = [go_file_json]
			else:
				jsons[pkg_name].append(go_file_json)

		#print dir_info["dir"]
		#print dir_info['files']
		#print "#%s#" % pkg_name
		if pkg_name in jsons:
			go_packages[pkg_name] = mergeGoSymbols(jsons[pkg_name])
			ip_packages[pkg_name] = dir_info["dir"]

	return "", ip_packages, go_packages

if __name__ == "__main__":
	go_dir = "/home/jchaloup/Packages/golang-github-glacjay-goini/fedora/golang-github-glacjay-goini/noarch/usr/share/gocode/src/github.com/glacjay/goini"
	go_dir = "/home/jchaloup/Packages/golang-github-rakyll-statik/fedora/golang-github-rakyll-statik/noarch/usr/share/gocode/src/github.com/rakyll/statik"
	go_dir = "/home/jchaloup/Packages/golang-googlecode-gomock/fedora/golang-googlecode-gomock/noarch/usr/share/gocode/src/code.google.com/p/gomock"

	ip_packages, go_packages = getSymbolsForImportPaths(go_dir)
	print go_packages
	print ip_packages



