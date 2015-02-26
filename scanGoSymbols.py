#!/bin/python

import optparse
from modules.GoSymbols import getSymbolsForImportPaths

def displaySymbols(symbols, all = False, stats = False):
	# types, funcs, vars
	if all:
		names = []
		for item in symbols["types"]:
			names.append(item["name"])
		for item in symbols["funcs"]:
			names.append(item["name"])
		for item in symbols["vars"]:
			names.append(item)

		if stats:
			print "  Total symbols: %s" % len(names)
		else:
			for item in sorted(names):
				print "  %s" % item

	else:
		names = []
		for item in symbols["types"]:
			names.append(item["name"])

		if stats:
			print "  Total types: %s" % len(names)
		else:
			for item in sorted(names):
				print "  type: %s" % item

		names = []
		for item in symbols["funcs"]:
			names.append(item["name"])

		if stats:
			print "  Total funcs: %s" % len(names)
		else:
			for item in sorted(names):
				print "  func: %s" % item

		names = []
		for item in symbols["vars"]:
			names.append(item)

		if stats:
			print "  Total vars:  %s" % len(names)
		else:
			for item in sorted(names):
				print "  var:  %s" % item

if __name__ == "__main__":

	parser = optparse.OptionParser("%prog [-l] dir")

        parser.add_option_group( optparse.OptionGroup(parser, "dir", "Directory to scan at.") )

	parser.add_option(
	    "", "-l", "--list", dest="list", action = "store_true", default = False,
	    help = "List all symbols for all import paths of a golang devel package."
	)

	parser.add_option(
	    "", "-p", "--prefix", dest="prefix", default = "",
	    help = "Prefix prepended to all listed import paths followed by slash /."
	)

	parser.add_option(
	    "", "-a", "--all", dest="all", action = "store_true", default = False,
	    help = "Normally symbols are prefixed by its type. This flag ignores the type and list all symbols as equal."
	)

	parser.add_option(
	    "", "-s", "--stats", dest="stats", action = "store_true", default = False,
	    help = "Don't list symbols, show their count for each import path instead."
	)


	options, args = parser.parse_args()

	if len(args) < 1:
		print "Synopsis: prog [-l] dir"
		exit(1)

	go_dir = args[0]

	prefix = ""
	if options.prefix != "":
		prefix = options.prefix + "/"

	if options.list:
		err, ip, symbols = getSymbolsForImportPaths(go_dir)
		if err != "":
			print err
			exit(1)
		for pkg in ip:
			print "Import path: %s%s" % (prefix, ip[pkg])
			displaySymbols(symbols[pkg], options.all, options.stats)

