#!/bin/python

###################################################################
# TODO:
# [  ] - detect more import paths/sources in spec file?
# [  ] - detect from %files every build, analyze its content (downloading it from koji byt detecting its name from spec file => no koji latest-builds, which packages/builds are no arch, which are arch specific (el6 beast)
# [  ] - all provides of source code import must in a form golang(import_path/...)
# [  ] - what files/provides are optional, which should not be in provides (test files, example, ...)
# [  ] - golang imports of examples are optional
###################################################################

from subprocess import PIPE
from subprocess import Popen
import sys
import os
import re
import optparse

import Repos

RPM_SCRIPTLETS = ('pre', 'post', 'preun', 'postun', 'pretrans', 'posttrans',
                  'trigger', 'triggerin', 'triggerprein', 'triggerun',
                  'triggerun', 'triggerpostun', 'verifyscript')

SECTIONS = ('build', 'changelog', 'check', 'clean', 'description', 'files',
               'install', 'package', 'prep') + RPM_SCRIPTLETS

script_dir = os.path.dirname(os.path.realpath(__file__))

def runCommand(cmd):
	#cmd = cmd.split(' ')
	process = Popen(cmd, stderr=PIPE, stdout=PIPE, shell=True)
	rt = process.returncode
	stdout, stderr = process.communicate()
	return stdout, stderr, rt

spec = sys.argv[1]

def readMacros(spec_lines = []):
	macros = {}
	for line in spec_lines:
		line = line.strip()
		if line == '' or  line.startswith((' ', '\t', '#', '\n')):
			continue

		if line.startswith('%global'):
			line = re.sub(r'[ \t]+', ' ', line)
			# %global <name> <body>
			parts = line.split(' ')
			macros[parts[1]] = parts[2]
			continue
	return macros

def reevalMacro(old_value, macros):
	value = ''
	# what macros are inside? %{...} or %...
	# no macro in macro use
	key = ''
	mfound = False
	mbracket = False
	for c in old_value:
		if c == '%':
			key = ''
			mfound = True
			continue
		if mfound:
			if c == '{':
				if not mbracket:
					mbracket = True
					continue
				else:
					return '', False
			if re.match('[a-zA-Z_]', c):
				key += c
			else:
				if key not in macros:
					return '', False
				value += macros[key]
				if not mbracket:
					mfound = False
					value += c
					continue
				if c != '}':
					return '', False
				mbracket = False
				mfound = False
		else:
			value += c
	return value, True

def evalMacro(name, macros):
	if name not in macros:
		return '', False
	
	value = ''
	evalue, rc = reevalMacro(macros[name], macros)
	if rc == False:
		return '', False

	while evalue != value:
		value = evalue
		evalue, rc = reevalMacro(value, macros)
		if rc == False:
			return '', False

	return value, True

def parseTags(spec_lines = []):
	tags = {}
	for line in spec_lines:
		line = re.sub(r'[ \t]+', ' ', line.strip())
		if line.upper().startswith('URL'):
			tags['url'] = line.split(' ')[1]
		if line.upper().startswith('NAME'):
			tags['name'] = line.split(' ')[1]
	return tags

def getRawSpecLines(spec):
	with open(spec, 'r') as file:
		return file.read().split('\n')

def getSpecLines(spec):
	stdout, stderr, rt = runCommand('rpmspec -P %s' % spec)
	if rt:
		return []
	return stdout.split('\n')

def getBuildsFromFilesSections(spec, pkg_name):
	stdout, stderr, rc = runCommand('rpmspec -P %s | grep "^%%files"' % spec)
	if rc != None:
		return []

	builds = []
	for line in stdout.split('\n'):
		if line != '':
			line = re.sub(r'[ \t]+', ' ', line)
			n_option = False
			n_value = ''
			name = ''
			items = line.split(' ')
			items_len = len(items)
			i = 1
			while i < items_len:
				item = items[i]
				i += 1
				# -n new_name
				if item == '-n':
					n_option = True
					n_value = items[i]
					#i += 1
					#continue
					break
				# -f file read list of files from file. We can skip this option.
				if item == '-f':
					i += 1
					continue
				# skip remaining options of any
				if item[0] == '-':
					continue
				# the non-option item is package's name
				name = item

			if n_option:
				builds.append(n_value)
			else:
				builds.append("%s-%s" % (pkg_name, name))

	return builds

def getProvidesFromPackageSections(spec, pkg_name):
	stdout, stderr, rc = runCommand('rpmspec -P %s' % spec)
	if rc != None:
		return []

	provides = {}
	in_package = False
	p_name = ''
	skip = False

	for line in stdout.split('\n'):
		if line == '':
			continue

		line = line.strip()
		for sec in SECTIONS:
			if line.lower().startswith("%%%s" % sec):
				if sec == 'package':
					in_package = True
					line = re.sub(r'[ \t]+', ' ', line)
					items = line.split(' ')
					items_len = len(items)
					i = 1
					while i < items_len:
						item = items[i]
						i += 1
						if item.startswith('-n'):
							p_name = items[i]
							break
						if item[0] == '-':
							continue
						p_name = '%s-%s' % (pkg_name, item)
						break

					provides[p_name] = []
					skip = True
				else:
					in_package = False
				break
		if skip:
			skip = False
			continue

		if in_package:
			if line.startswith('Provides'):
				line = re.sub(r'[ \t]+', ' ', line)
				provides[p_name].append(line.split(' ')[1])

	return provides

def loadImportPaths():
	lines = []
	with open('%s/golang.import_paths' % script_dir, 'r') as file:
		lines = file.read().split('\n')

	import_paths = {}
	for line in lines:
		parts = line.split(':')
		if len(parts) != 2:
			continue

		import_paths[parts[0]] = []
		field = parts[1].split(',')
		for item in field:
			import_paths[parts[0]].append(item.strip())

	return import_paths

class SpecTest:

	def __init__(self, spec):
		self.spec = spec
		# get spec lines (not evaluated and evaluated)
		self.lines = getRawSpecLines(spec)
		self.plines = getSpecLines(spec)
		# read macros
		self.macros = readMacros(self.lines)
		# read some tags
		self.tags = parseTags(self.plines)
		url = self.tags['url']
		self.repo, self.url = Repos.detectKnownRepos(url)
		self.import_paths = {}
		v, rc = evalMacro('import_path', self.macros)
		if rc:
			self.import_paths['%s-devel' % (self.tags['name'])] = v

##################################
# TESTS
##################################
	def testImportPath(self, verbose = False):
		import_path, rc = evalMacro('import_path', self.macros)
		if rc == False:
			print "E: missing %global import_path ..."
			return 1
		if verbose:
			print "import_path detected: %s" % import_path
		return 0

	def testPackageName(self, verbose = False):
		pkg_name = ''
		if self.repo == Repos.GITHUB:
			pkg_name = Repos.github2pkgdb(self.url)
		elif self.repo == Repos.GOOGLECODE:
			pkg_name = Repos.googlecode2pkgdb(self.url)
		elif self.repo == Repos.GOLANGORG:
			pkg_name = Repos.golangorg2pkgdb(self.url)
	#	elif self.repo == Repos.GOPKG:
	#		pkg_name = Repos.gopkg2pkgdb(url)

		name = self.tags['name']
		if pkg_name == '':
			if verbose:
				print 'Uknown repo url'
			return 0

		if pkg_name != name:
			print "W: Incorrect package name, should be %s" % pkg_name
			return 1
		if verbose:
			print "Correct package name: %s" % pkg_name

		return 0

	def testCommit(self, verbose = False):
		commit_label = 'commit'
		if self.repo == Repos.GOOGLECODE:
			commit_label = 'rev'

		commit, rc = evalMacro(commit_label, self.macros)
		if rc == False:
			print "E: missing %global %s ..." % commit_label
			return 1
		if verbose:
			print "%s detected: %s" % (commit_label, commit)
		return 0

	def testBuilds(self, verbose = False):
		errors = 0
		pkg_name = self.tags['name']
		builds = getBuildsFromFilesSections(self.spec, pkg_name)

		local_ips = loadImportPaths()

		# read all possible builds
		provides = getProvidesFromPackageSections(self.spec, pkg_name)
		# here filter only devel subpackages
		for key in provides:
			if key not in builds:
				if verbose:
					print "Skipping %s, not in builds" % key
				continue

			if not key.endswith('devel'):
				if verbose:
					print "Skipping %s, name does not end with devel sufix" % key
				continue

			if verbose:
				print "Checking Provides of %s package:" % key
			ip = []
			if key in self.import_paths:
				ip = [self.import_paths[key]]
			elif key in local_ips:
				if verbose:
					print "Taking import path from golang.import_paths"
				ip = local_ips[key]
			elif verbose:
				print "Import path for this package unknown"

			for provide in provides[key]:
				if not provide.startswith('golang('):
					print "E: Provides does not start with golang(: %s" % provide
					errors += 1
					continue
				if provide[-1] != ')':
					print "E: Provides does not end with ): %s" % provide
					errors += 1
					continue
				if ip != []:
					found = False
					for path in ip:
						if provide[7:-1].startswith(path):
							found = True
							break

					if not found:
						print "E: Provides does not start with any of import paths %s: %s" % (', '.join(ip), provide)
						errors += 1
						continue
				if verbose:
					print "Provides %s correct" % provide
				
		return errors

##################################
# MAIN
##################################
if __name__ == '__main__':

	parser = optparse.OptionParser("%prog [-v]")

#        parser.add_option_group( optparse.OptionGroup(parser, "file", "Xml file with scanned results") )

	parser.add_option(
	    "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
	    help = "Display more information"
	)

	options, args = parser.parse_args()

	errors = 0
	warnings = 0
	verbose = options.verbose

	specTestObj = SpecTest(spec)
	#########
	# TESTS #
	#########

	# 1. check package name
	warnings += specTestObj.testPackageName(verbose)
	# 2. check for %global import_path ...
	errors += specTestObj.testImportPath(verbose)
	# 3. check for %global commit ... #
	errors += specTestObj.testCommit(verbose)
	# 4.
	errors += specTestObj.testBuilds(verbose)

	###########
	# Summary #
	###########
	print "%s specfiles checked; %s errors, %s warnings." % (1, errors, warnings)

