#!/bin/python

import os
import re
from Utils import getScriptDir
from modules.Repos import detectGithub, detectGooglecode, detectGolangorg, detectGoogleGolangorg, detectGopkg
from modules.Repos import github2pkgdb, googlecode2pkgdb, googlegolangorg2pkgdb, golangorg2pkgdb 
from Config import Config

GOLANG_IMPORTS = "data/golang.imports"

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
		# import must be followed by white space
		content = re.sub(r'import[^\s]', '######', content)

		start = content.find('import')
		if start == -1:
			return []

		# import grammar: http://golang.org/ref/spec#Import_declarations
		#
		# ImportDecl       = "import" ( ImportSpec | "(" { ImportSpec ";" } ")" ) .
		# ImportSpec       = [ "." | PackageName ] ImportPath .
		# ImportPath       = string_lit .

		# make sure import is always followed only by one space
		content = re.sub(r'import[^("]+', 'import ', content)
		# replace ; with newline
		content = re.sub(';', '\n', content)
		# deal with one liners
		p = re.compile(r'import\s+"([^"]+)"')
		content = p.sub(r'import ("\1")', content)
		# get string in a form: import ([^)]*)
		end = content.find(')', start)
		imports = content[start+6:end]
		start = imports.find('(')
		imports = imports[start+1:].strip()

		imps = []
		for pot_imp in imports.split('\n'):
			if pot_imp == "":
				continue

			pot_imp = pot_imp.strip()
			pot_imp = re.sub(r'\s+', ' ', pot_imp)

			# get rid of PackageName and "."
			parts = pot_imp.split(' ')
			if len(parts) == 2:
				pot_imp = parts[1]

			if '"' in pot_imp:
				pot_imp = re.sub('"', '', pot_imp)

			# If the import path starts with . or /,
			# it is relative or absolute path.
			# Filter it out.
			if pot_imp == "" or pot_imp[0] == "." or pot_imp[0] == "/":
				continue

			imps.append(pot_imp)

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

def getNativeImports():
	script_dir = getScriptDir() + "/.."
	with open('%s/%s' % (script_dir, GOLANG_IMPORTS), 'r') as file:
                content = file.read()
		return content.split('\n')

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
		elif gimport.startswith('google.golang.org'):
			key = detectGoogleGolangorg(gimport)
		elif gimport.startswith('gopkg.in'):
			key = detectGopkg(gimport)
		else:
			key = "Unknown"

		if key not in classes:
			classes[key] = [gimport]
		else:
			classes[key].append(gimport)

	return classes

def loadImportPathDb():
	db_file = Config().getImportPathDb()
	lines = []
	with open(db_file, 'r') as file:
		lines = file.read().split('\n')

	ip_provides = {}
	ip_imports = {}
	pkg_devel_main_pkg = {}

	for line in lines:
		line = line.strip()

		if line == "" or line[0] == "#":
			continue

		if line.startswith("Provides") or line.startswith("Imports:"):
			parts = line.split(":")
			if len(parts) != 4:
				continue

			if len(parts[1]) == 0 or len(parts[2]) == 0:
				continue

			#Provides|Import:pkg_name:pkg_devel_name:import_path
			pkg_name	= parts[1].strip()
			pkg_devel_name	= parts[2].strip()
			import_path	= parts[3].strip()

			if line.startswith("Provides:"):
				ip_provides[ pkg_devel_name ] = import_path.split(",")
			else:
				ip_imports[ pkg_devel_name ] = import_path.split(",")

			if pkg_devel_name not in pkg_devel_main_pkg:
				pkg_devel_main_pkg[pkg_devel_name] = pkg_name

		else:
			continue			

	return (ip_provides, ip_imports, pkg_devel_main_pkg)

def getDevelImportedPaths():
	_, ip_i, _ = loadImportPathDb()
	return ip_i

def getDevelProvidedPaths():
	ip_p, _, _ = loadImportPathDb()
	return ip_p

