# ####################################################################
# gofed - set of tools to automize packaging of golang devel codes
# Copyright (C) 2014  Jan Chaloupka, jchaloup@redhat.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# ####################################################################

###################################################################
# TODO:
# [  ] - detect more import paths/sources in spec file?
# [  ] - detect from %files every build, analyze its content (downloading it from koji by detecting its name
#        from spec file => no koji latest-builds, which packages/builds are no arch, which are arch specific (el6 beast)
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
import tempfile

import Utils
import Repos

from Utils import runCommand
from ImportPath import ImportPath
from Config import Config

RPM_SCRIPTLETS = ('pre', 'post', 'preun', 'postun', 'pretrans', 'posttrans',
                  'trigger', 'triggerin', 'triggerprein', 'triggerun',
                  'triggerun', 'triggerpostun', 'verifyscript')

SECTIONS = ('build', 'changelog', 'check', 'clean', 'description', 'files',
               'install', 'package', 'prep') + RPM_SCRIPTLETS

class SpecInfo:

	def __init__(self, spec):
		self.spec = spec
		lines = self.getRawSpecLines(spec)
		plines = self.getSpecLines(spec)
		# read macros
		self.macros = self.readMacros(lines)
		# read some tags
		self.tags = self.parseTags(plines)

	def getMacro(self, name):
		if name not in self.macros:
			return ""
		else:
			value, ok = self.evalMacro(name, self.macros)
			if ok:
				return value
			else:
				return ""

	def getTag(self, name):
		if name not in self.tags:
			return ""
		else:
			return self.tags[name]

	def readMacros(self, spec_lines = []):
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

	def reevalMacro(self, old_value, macros):
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

	def evalMacro(self, name, macros):

		if name not in macros:
			return "", False	
		value = ""

		evalue, rc = self.reevalMacro(macros[name], macros)
		if rc == False:
			return '', False

		while evalue != value:
			value = evalue
			evalue, rc = self.reevalMacro(value, macros)
			if rc == False:
				return '', False

		return value, True

	def parseTags(self, spec_lines = []):
		tags = {}
		for line in spec_lines:
			line = re.sub(r'[ \t]+', ' ', line.strip())
			if line.upper().startswith('URL'):
				tags['url'] = line.split(' ')[1]
				continue
			if line.upper().startswith('NAME'):
				tags['name'] = line.split(' ')[1]
				continue
			if line.upper().startswith('SUMMARY'):
				if "summary" not in tags:
					tags['summary'] = " ".join(line.split(' ')[1:])
				continue
			if line.upper().startswith('SOURCE'):
				src = line[6:].strip()
				# now number or : follows
				if src[0] == ':':
					tags['source0'] = src[1:].strip()
				else:
					items = src.split(':')
					tags['source%s' % items[0].strip()] = ':'.join(items[1:]).strip()
		return tags

	def getRawSpecLines(self, spec):
		with open(spec, 'r') as file:
			return file.read().split('\n')

	def getSpecLines(self, spec):
		stdout, stderr, rt = Utils.runCommand('rpmspec -P %s' % spec)
		if rt != 0:
			return []
		return stdout.split('\n')

	def getProvidesFromPackageSections(self, spec, pkg_name):
		stdout, stderr, rc = Utils.runCommand('rpmspec -P %s' % spec)
		if rc != 0:
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

def fetchProvides(pkg, branch):
	"""Fetch a spec file from pkgdb and get provides from all its [sub]packages

	Keyword arguments:
	pkg -- package name
	branch -- branch name
	"""
	f = tempfile.NamedTemporaryFile(delete=True)
	runCommand("curl http://pkgs.fedoraproject.org/cgit/%s.git/plain/%s.spec > %s" % (pkg, pkg, f.name))
	provides = SpecInfo(f.name).getProvidesFromPackageSections(f.name, pkg)
	f.close()
	return provides



def loadImportPaths():
	lines = []
	golang_secondary_ips_path = Config().getGolangSecondaryIPs()
	with open(golang_secondary_ips_path, 'r') as file:
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

def loadSubpackageSourceMapping():
	lines = []
	golang_secondary_ips_path = Config().getGolangSecondaryIPs()
	with open(golang_secondary_ips_path, 'r') as file:
		lines = file.read().split('\n')

	sources = {}
	for line in lines:
		parts = line.split(':')
		if len(parts) != 2:
			continue

		sources[parts[0]] = []
		field = parts[1].split(',')
		for item in field:
			sources[parts[0]].append(item.strip())

	return sources



def fetchPkgInfo(pkg, branch):
	"""Fetch a spec file from pkgdb and get its commit

	Keyword arguments:
	pkg -- package name
	branch -- branch name
	"""
	f = tempfile.NamedTemporaryFile(delete=True)
	Utils.runCommand("curl http://pkgs.fedoraproject.org/cgit/%s.git/plain/%s.spec > %s" % (pkg, pkg, f.name))
	spec_info = SpecInfo(f.name)
	info = {}
	commit = spec_info.getMacro('commit')
	if commit == "":
		commit = spec_info.getMacro('rev')

	info["commit"] = commit
	info["url"] = spec_info.getTag("url")

	f.close()
	return info

def getPackageCommits(pkg):
	info = fetchPkgInfo(pkg, 'master')
	return info["commit"] 

def getPkgURL(pkg, branch = "master"):
	info = fetchPkgInfo(pkg, 'master')
	return info["url"] 


