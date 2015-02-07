#!/bin/python

# ####################################################################
# go2fed - set of tools to automize packaging of golang devel codes
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

import sys
import re
import os
import urllib2
import optparse
from subprocess import Popen, PIPE
import Utils

def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

# get imports from a file
def getFileImports(gofile):

	with open(gofile, 'r') as file:
		content = file.read()

		# delete one line comments
		content = re.sub(r'//[^\n]*\n', '\n', content)
		# delete multi-line comments
		p = re.compile(r'/\*.+?\*/', re.DOTALL)
		content = p.sub('\n', content)
		# delete all "import" strings
		content = re.sub(r'"import"', '', content)

		start = content.find('import')
		if start == -1:
			return []

		# import grammar: http://golang.org/ref/spec#Import_declarations
		#
		# ImportDecl       = "import" ( ImportSpec | "(" { ImportSpec ";" } ")" ) .
		# ImportSpec       = [ "." | PackageName ] ImportPath .
		# ImportPath       = string_lit .

		# get rid of PackageName and "."
		content = re.sub(r'import[^("]+', 'import ', content)
		# replace ; with newline
		content = re.sub(';', '\n', content)

		p = re.compile(r'import\s+"([^"]+)"')
		content = p.sub(r'import ("\1")', content)

		end = content.find(')', start)
		imports = content[start+6:end]
		start = imports.find('(')
		imports = imports[start+1:].strip()

		imps = []
		for pot_imp in re.sub(r'\s+', ' ', imports).split(' '):
			if '"' in pot_imp:
				imps.append(re.sub('"', '', pot_imp))

		return imps

# get imports from all files in the directory (or actual directory), sort -u them
def getFileTreeImports(directory):
	imports = []
	for dirName, subdirList, fileList in os.walk(directory):
		for fname in fileList:
			# filter all non *.go files
			if fname.endswith(".go"):
				imports = imports + getFileImports(dirName + "/" + fname)

	return sorted(list(set(imports)))
	# Only for test purposes
	for item in sorted(list(set(imports))):
		print item

# for the given list of imports, divide them into
# classes (native, github, googlecode, bucket, ...)
def getNativeImports():
	script_dir = getScriptPath()
	with open('%s/golang.imports' % script_dir, 'r') as file:
                content = file.read()
		return content.split('\n')

def getMappings():
	script_dir = getScriptPath()
        with open('%s/golang.mapping' % script_dir, 'r') as file:
		maps = {}
                content = file.read()
		for line in content.split('\n'):
			if line == "" or line[0] == '#':
				continue
			line = re.sub(r'[\t ]+', ' ', line).split(' ')
			if len(line) != 2:
				continue
			maps[line[0]] = line[1]
				
		return maps

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

def decomposeImports(imports):
	classes = {}
	native = getNativeImports()
	for gimport in imports:
		prefix = gimport.split('/')[0]
		if prefix in native:
			key = "Native"
		elif gimport.startswith('github.com'):
			key = detectGithub(gimport)
		elif gimport.startswith('code.google.com'):
			key = detectGooglecode(gimport)
		elif gimport.startswith('golang.org'):
			key = detectGolangorg(gimport)
		elif gimport.startswith('gopkg.in'):
			key = detectGopkg(gimport)
		else:
			key = "Unknown"

		if key not in classes:
			classes[key] = [gimport]
		else:
			classes[key].append(gimport)

	return classes

# for every class, detect if it is already in pkgdb
def packageInPkgdb(pkg):
	cmd = "git ls-remote http://pkgs.fedoraproject.org/cgit/" + pkg + ".git/"
	p = Popen(cmd , shell=True, stdout=PIPE, stderr=PIPE)
	out, err = p.communicate()

	if p.returncode == 0:
		return True

	return False

if __name__ == "__main__":
	parser = optparse.OptionParser("%prog [-a] [-c] [-d] [directory]")

	parser.add_option_group( optparse.OptionGroup(parser, "directory", "Directory to inspect. If empty, current directory is used.") )

	parser.add_option(
	    "", "-a", "--all", dest="all", action = "store_true", default = False,
	    help = "Display all imports including golang native"
	)

	parser.add_option(
            "", "-c", "--classes", dest="classes", action = "store_true", default = False,
            help = "Decompose imports into classes"
        )

	parser.add_option(
            "", "-d", "--pkgdb", dest="pkgdb", action = "store_true", default = False,
            help = "Check if a class is in the PkgDB (only with -c option)"
        )

	parser.add_option(
            "", "-s", "--short", dest="short", action = "store_true", default = False,
            help = "Display just classes without its imports"
        )

	options, args = parser.parse_args()

	path = "."
	if len(args):
		path = args[0]

	classes = decomposeImports(getFileTreeImports(path))
	mappings = getMappings()
	for element in classes:
		if not options.all and element == "Native":
			continue

		pkg_name = ""
		if element.startswith('github.com'):
			key = detectGithub(element)
			if key in mappings:
				pkg_name = mappings[key]
			else:
				pkg_name = github2pkgdb(element)
		elif element.startswith('code.google.com'):
			key = detectGooglecode(element)
			if key in mappings:
				pkg_name = mappings[key]
			else:
				pkg_name = googlecode2pkgdb(element)
		elif element.startswith('golang.org'):
			key = detectGolangorg(element)
                        if key in mappings:
                                pkg_name = mappings[key]
                        else:
                                pkg_name = googlecode2pkgdb(element)
		elif element.startswith('gopkg.in'):
			key = detectGopkg(element)
			if key in mappings:
                                pkg_name = mappings[key]

		pkg_in_pkgdb = False
		if options.classes:
			if options.pkgdb and pkg_name != "":
				pkg_in_pkgdb = packageInPkgdb(pkg_name)
				if pkg_in_pkgdb:
					print (Utils.GREEN + "Class: %s (%s) PkgDB=%s" + Utils.ENDC) % (element, pkg_name, pkg_in_pkgdb)
				else:
					print (Utils.RED + "Class: %s (%s) PkgDB=%s" + Utils.ENDC ) % (element, pkg_name, pkg_in_pkgdb)
			else:
				print "Class: %s" % element
		if not options.classes or not options.short:
			for gimport in classes[element]:
				print "\t%s" % gimport
			if options.classes:
				print ""

