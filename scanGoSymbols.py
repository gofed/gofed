import optparse
from modules.GoSymbols import PackageToXml, ProjectToXml
import json
from modules.GoSymbolsExtractor import GoSymbolsExtractor
from modules.Config import Config

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

def setOptionParser():

	parser = optparse.OptionParser("%prog -l|-u|-p [-a] [-s] [-x] dir")

        parser.add_option_group( optparse.OptionGroup(parser, "dir", "Directory to scan at.") )

	parser.add_option(
	    "", "-l", "--list", dest="list", action = "store_true", default = False,
	    help = "List all symbols for all import paths of a golang devel package."
	)

	parser.add_option(
	    "", "", "--prefix", dest="prefix", default = "",
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

	parser.add_option(
	    "", "-x", "--xml", dest="xml", action = "store_true", default = False,
	    help = "List symbols in xml format."
	)

	parser.add_option(
	    "", "-u", "--usedip", dest="usedip", action = "store_true", default = False,
	    help = "List all imported paths/packages."
	)

	parser.add_option(
	    "", "-p", "--provides", dest="provides", action = "store_true", default = False,
	    help = "List all provided import paths."
	)

	parser.add_option(
            "", "", "--scan-all-dirs", dest="scanalldirs", action = "store_true", default = False,
            help = "Scan all dirs, including Godeps directory"
        )

	parser.add_option(
            "", "", "--skip-dirs", dest="skipdirs", default = "",
            help = "Scan all dirs except specified via SKIPDIRS. Directories are comma separated list."
        )

	parser.add_option(
            "", "", "--pure-xml", dest="purexml", action = "store_true", default = False,
            help = "Print all packages in one xml file"
        )

	parser.add_option(
            "", "", "--skip-errors", dest="skiperrors", action = "store_true", default = False,
            help = "Skip all errors during Go symbol parsing"
        )

	return parser


if __name__ == "__main__":

	parser = setOptionParser()

	options, args = parser.parse_args()

	if len(args) < 1:
		print "Synopsis: prog -l|-u|-p [-a] [-s] [-x] dir"
		exit(1)

	go_dir = args[0]

	prefix = ""
	if options.prefix != "":
		prefix = options.prefix + "/"

	if not options.scanalldirs:
		noGodeps = Config().getSkippedDirectories()
	else:
		noGodeps = []

	if options.skipdirs:
		for dir in options.skipdirs.split(','):
			dir = dir.strip()
			if dir == "":
				continue
			noGodeps.append(dir)

	#obj = ProjectToXml(options.prefix, go_dir)
	#print obj
	#print obj.getError()
	#exit(0)

	gse_obj = GoSymbolsExtractor(go_dir, skip_errors=options.skiperrors, noGodeps=noGodeps)
	if not gse_obj.extract():
		print gse_obj.getError()
		exit(1)

	if options.provides:
		ip = gse_obj.getSymbolsPosition()
		ips = []
		for pkg in ip:
			ips.append(ip[pkg])

		for ip in sorted(ips):
			if ip == "." and options.prefix != "":
				print options.prefix
			else:
				print "%s%s" % (prefix, ip)

	elif options.list:
		ip = gse_obj.getSymbolsPosition()
		symbols = gse_obj.getSymbols()
		ip_used = gse_obj.getImportedPackages()

		if options.purexml:
			print "<?xml version='1.0' encoding='ASCII'?>"
			print "<project ipprefix=\"%s\" commit=\"\" nvr=\"\">" % options.prefix
			print "<packages>"

		for pkg in ip:
			if not options.purexml:
				print "Import path: %s%s" % (prefix, ip[pkg])
			#print json.dumps(symbols[pkg])
			if options.xml:
				obj = PackageToXml(symbols[pkg], "%s%s" % (prefix, ip[pkg]),  imports=False)
				if obj.getStatus():
					print obj#.getError()
				else:
					print obj.getError()
					exit(0)
			else:
				displaySymbols(symbols[pkg], options.all, options.stats)

		if options.purexml:
			print "</packages>"
			print "</project>"

	elif options.usedip:
		ip_used = gse_obj.getImportedPackages()

		for uip in sorted(ip_used):
			print uip

