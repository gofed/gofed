#!/bin/python
#
# TODO:
# [  ] - filter out imports in comments, golang-github-spf13-pflag flag.go for example

import sys
import re

if len(sys.argv) < 2:
	exit(0)

with open(sys.argv[1], 'r') as file:
	content = file.read()
	start = content.find('import')

	if start == -1:
		exit(0)

	# we can have import ( ... ) or import "..."
	p = re.compile(r'import\s+"([^"]+)"')
	content = p.sub(r'import ("\1")', content) 

	end = content.find(')', start)
	imports = content[start+6:end]
	start = imports.find('(')
	imports = imports[start+1:].strip()

	print re.sub(r'\s+', '\n', imports)

