# Check difference of APIs of two commits

# Output is number of symbols added and removed.
# You can list of those symbols as well

# Projects that change exported symbols with each commit should not be used
# as a built or install time dependency until they stabilize.

import optparse
from modules.GoSymbols import CompareSourceCodes
from modules.Utils import YELLOW, RED, BLUE, ENDC
from os import path

MSG_NEG=1
MSG_POS=2
MSG_NEUTRAL=4

def displayApiDifference(status, color=True, msg_type=MSG_POS & MSG_NEUTRAL & MSG_NEG, prefix=""):
	spkgs = sorted(status.keys())
	for pkg in spkgs:
		lines = []
		for msg in status[pkg]:
			if msg[0] == "-":
				if msg_type & MSG_NEG > 0:
					if color:
						lines.append("\t%s%s%s" % (RED, msg, ENDC))
					else:
						lines.append("\t%s" % msg)
			elif msg[0] == "+":
				if msg_type & MSG_POS > 0:
					if color:
						lines.append("\t%s%s%s" % (BLUE, msg, ENDC))
					else:
						lines.append("\t%s" % msg)
			else:
				if msg_type & MSG_NEUTRAL > 0:
					lines.append("\t%s" % msg)

		if lines != []:
			if prefix != "":
				if pkg == ".":
					pkg = prefix
				else:
					pkg = "%s/%s" % (prefix, pkg)
			if color:
				print "%sPackage: %s%s" % (YELLOW, pkg, ENDC)
			else:
				print "Package: %s" % pkg

			for line in lines:
				print line

if __name__ == "__main__":

	parser = optparse.OptionParser("prog [-e] [-d] DIR1 DIR2")

        parser.add_option_group( optparse.OptionGroup(parser, "DIR1", "Directory with old source codes") )
        parser.add_option_group( optparse.OptionGroup(parser, "DIR2", "Directory with new source codes") )

	parser.add_option(
	    "", "-c", "--color", dest="color", action = "store_true", default = False,
	    help = "Color output."
	)

	parser.add_option(
	    "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
	    help = "Verbose mode."
	)

	parser.add_option(
	    "", "-e", "--error", dest="error", action = "store_true", default = False,
	    help = "Show errors only."
	)

	parser.add_option(
	    "", "-a", "--all", dest="all", action = "store_true", default = False,
	    help = "Show all differences between APIs"
	)

	parser.add_option(
	    "", "", "--prefix", dest="p", default = "",
	    help = "Import paths prefix"
	)

	parser.add_option(
	    "", "", "--old-xml", dest="oldxml", default = "",
	    help = "Use old symbols from xml"
	)

	parser.add_option(
	    "", "", "--new-xml", dest="newxml", default = "",
	    help = "Use new symbols from xml"
	)

	options, args = parser.parse_args()

	if options.p != "" and options.p[-1] == '/':
		print "Error: --prefix can not end with '/'"
		exit(1)

	missing_args = 2
	# file exists?
	if options.oldxml != "":
		if not path.exists(options.oldxml):
			print "Error: %s does not exists" % options.oldxml
			exit(1)
		missing_args = missing_args - 1

	# file exists?
	if options.newxml != "":
		if not path.exists(options.newxml):
			print "Error: %s does not exists" % options.newxml
			exit(1)
		missing_args = missing_args - 1

	if missing_args == 2:
		if len(args) < 2:
			print "Missing DIR1 or DIR2"
			exit(1)
	if missing_args == 1:
		if len(args) < 1:
			print "Missing DIR"
			exit(1)

	# 1) check if all provided import paths are the same
	# 2) check each package for new/removed/changed symbols
	cmp_src = CompareSourceCodes()
	if options.oldxml != "" and options.newxml != "":
		cmp_src.compareXmls(options.oldxml, options.newxml)
	elif options.newxml != "":
		cmp_src.compareDirXml(args[0], options.newxml)
	elif options.oldxml != "":
		cmp_src.compareXmlDir(options.oldxml, args[0])
	else:
		cmp_src.compareDirs(args[0], args[1])

	for e in cmp_src.getError():
		print "Error: %s" % e

	if not options.error:
		status = cmp_src.getStatus()
		msg_type = MSG_NEG
		if options.all:
			msg_type = MSG_POS | MSG_NEUTRAL | MSG_NEG
		elif options.verbose:
			msg_type = MSG_POS | MSG_NEG

		displayApiDifference(status, options.color, msg_type, options.p)
