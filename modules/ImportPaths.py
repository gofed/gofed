#!/bin/python

import os
import re
from Utils import getScriptDir
from modules.Repos import detectGithub, detectGooglecode, detectGolangorg, detectGoogleGolangorg, detectGopkg
from modules.Repos import github2pkgdb, googlecode2pkgdb, googlegolangorg2pkgdb, golangorg2pkgdb 

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

