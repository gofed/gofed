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

import sys
import re
import os
import urllib2
import optparse
from subprocess import Popen, PIPE
from modules.Utils import GREEN, RED, ENDC
from modules.Packages import packageInPkgdb
from modules.Utils import FormatedPrint
from modules.ImportPath import ImportPath
from modules.ImportPathsDecomposer import ImportPathsDecomposer
from modules.GoSymbolsExtractor import GoSymbolsExtractor
from modules.Config import Config

if __name__ == "__main__":
	parser = optparse.OptionParser("%prog [-a] [-c] [-d [-v]] [directory]")

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
            "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
            help = "Show all packages if -d option is on"
        )

	parser.add_option(
            "", "-s", "--short", dest="short", action = "store_true", default = False,
            help = "Display just classes without its imports"
        )

	parser.add_option(
            "", "", "--spec", dest="spec", action = "store_true", default = False,
            help = "Display import path for spec file"
        )

	parser.add_option(
            "", "-r", "--requires", dest="requires", action = "store_true", default = False,
            help = "Use Requires instead of BuildRequires. Used only with --spec option."
        )

	parser.add_option(
            "", "", "--skip-errors", dest="skiperrors", action = "store_true", default = False,
            help = "Skip all errors during Go symbol parsing"
        )

	parser.add_option(
            "", "", "--importpath", dest="importpath", default = "",
            help = "Don't display class belonging to IMPORTPATH prefix"
        )

	parser.add_option(
            "", "", "--scan-all-dirs", dest="scanalldirs", action = "store_true", default = False,
            help = "Scan all dirs, including Godeps directory"
        )

	parser.add_option(
            "", "", "--skip-dirs", dest="skipdirs", default = "",
            help = "Scan all dirs except specified via SKIPDIRS. Directories are comma separated list."
        )

	options, args = parser.parse_args()

	path = "."
	if len(args):
		path = args[0]

	fmt_obj = FormatedPrint()

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

	gse_obj = GoSymbolsExtractor(path, imports_only=True, skip_errors=options.skiperrors, noGodeps=noGodeps)
	if not gse_obj.extract():
		fmt_obj.printError(gse_obj.getError())
		exit(1)

	ip_used = gse_obj.getImportedPackages()
	ipd = ImportPathsDecomposer(ip_used)
	if not ipd.decompose():
		fmt_obj.printError(ipd.getError())
		exit(1)

	warn = ipd.getWarning()
	if warn != "":
		fmt_obj.printWarning("Warning: %s" % warn)

	classes = ipd.getClasses()
	sorted_classes = sorted(classes.keys())

	for element in sorted_classes:
		if not options.all and element == "Native":
			continue

		# class name starts with prefix => filter out
		if options.importpath != "" and element.startswith(options.importpath):
			continue

		# filter out all members of a class prefixed by prefix
		gimports = []
		for gimport in classes[element]:
			if options.importpath != "" and gimport.startswith(options.importpath):
				continue
			gimports.append(gimport)

		if gimports == []:
			continue

		if options.classes:
			# Native class is just printed
			if options.all and element == "Native":
				# does not make sense to check Native class in PkgDB
				if options.pkgdb:
					continue
				print "Class: %s" % element
				if not options.short:
					for gimport in gimports:
						print "\t%s" % gimport
				continue

			# Translate non-native class into package name (if -d option)
			if options.pkgdb:
				ip_obj = ImportPath(element)
				if not ip_obj.parse():
					fmt_obj.printWarning("Unable to translate %s to package name" % element)
					continue

				pkg_name = ip_obj.getPackageName()
				if pkg_name == "":
					fmt_obj.printWarning(ip_obj.getError())

				pkg_in_pkgdb = packageInPkgdb(pkg_name)
				if pkg_in_pkgdb:
					if options.verbose:
						print (GREEN + "Class: %s (%s) PkgDB=%s" + ENDC) % (element, pkg_name, pkg_in_pkgdb)
				else:
					print (RED + "Class: %s (%s) PkgDB=%s" + ENDC ) % (element, pkg_name, pkg_in_pkgdb)
				continue

			# Print class
			print "Class: %s" % element
			if not options.short:
				for gimport in sorted(gimports):
					print "\t%s" % gimport
			continue

		# Spec file BR
		if options.spec:
			for gimport in classes[element]:
				if options.requires:
					print "Requires: golang(%s)" % gimport
				else:
					print "BuildRequires: golang(%s)" % gimport
			continue

		# Just a list of all import paths
		for gimport in sorted(classes[element]):
			print "\t%s" % gimport
