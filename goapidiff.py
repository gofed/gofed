#!/bin/python

# Check difference of APIs of two commits

# Output is number of symbols added and removed.
# You can list of those symbols as well

# Projects that change exported symbols with each commit should not be used
# as a built or install time dependency until they stabilize.

import optparse
from modules.GoSymbols import getSymbolsForImportPaths, PackageToXml, ProjectToXml, ComparePackages

if __name__ == "__main__":

	parser = optparse.OptionParser("%prog [-e] [-d] DIR1 DIR2")

        parser.add_option_group( optparse.OptionGroup(parser, "file", "Xml file with scanned results") )

	parser.add_option(
	    "", "-d", "--detail", dest="detail", action = "store_true", default = False,
	    help = "Display more information about affected branches"
	)

	parser.add_option(
	    "", "-e", "--executable", dest="executables", action = "store_true", default = False,
	    help = "Include executables in summary"
	)

	options, args = parser.parse_args()
	if len(args) != 2:
		print "Missing DIR1 or DIR2"
		exit(1)

	go_dir1 = args[0]
	go_dir2 = args[1]

	# 1) check if all provided import paths are the same
	# 2) check each package for new/removed/changed symbols

	err, ip1, symbols1, ip_used2 = getSymbolsForImportPaths(go_dir1)
	if err != "":
		print "%s: %s" % (go_dir1, err)
		exit(1)

	err, ip2, symbols2, ip_used2 = getSymbolsForImportPaths(go_dir2)
	if err != "":
		print "%s: %s" % (go_dir2, err)
		exit(1)

	ip1_set = set(ip1.keys())
	ip2_set = set(ip2.keys())

	new_ips = list( ip2_set - ip1_set )
	rem_ips = list( ip1_set - ip2_set )
	com_ips = sorted(list( ip1_set & ip2_set ))

	# list new packages
	if new_ips != []:
		print "+new packages: " + str(new_ips)

	# list removed packages
	if rem_ips != []:
		print "-removed packages: " + str(rem_ips)

	# compare common packages
	for pkg in com_ips:
		obj1 = PackageToXml(symbols1[pkg], "%s" % (ip1[pkg]), imports=False)
		if not obj1.getStatus():
			print obj1.getError()

		obj2 = PackageToXml(symbols2[pkg], "%s" % (ip2[pkg]), imports=False)
		if not obj2.getStatus():
			print obj2.getError()

		ComparePackages(pkg.split(":")[0]).comparePackages(obj1.getPackage(), obj2.getPackage())

