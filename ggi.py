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
from modules.Utils import GREEN, RED, ENDC
from modules.Utils import FormatedPrint
from modules.Config import Config
from modules.ParserConfig import ParserConfig

from gofed_infra.system.core.factory.actfactory import ActFactory
from gofed_lib.go.importpath.decomposerbuilder import ImportPathsDecomposerBuilder
from gofed_lib.go.projectinfobuilder import ProjectInfoBuilder
from gofed_lib.distribution.clients.pkgdb.client import PkgDBClient
from gofed_infra.system.artefacts.artefacts import ARTEFACT_GOLANG_PROJECT_PACKAGES
from gofed_lib.distribution.packagenamegeneratorbuilder import PackageNameGeneratorBuilder


import logging

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

	parser.add_option(
            "", "", "--all-occurrences", dest="alloccurrences", action = "store_true", default = False,
            help = "List imported paths in all packages including main. Default is skip main packages."
        )

	parser.add_option(
            "", "", "--show-occurrence", dest="showoccurrence", action = "store_true", default = False,
            help = "Show occurence of import paths."
        )

	parser.add_option(
            "", "", "--show-main", dest="showmain", action = "store_true", default = False,
            help = "Show occurence of import paths in main packages only (+means not just main)."
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

	parser_config = ParserConfig()
	if options.skiperrors:
		parser_config.setSkipErrors()
	parser_config.setNoGodeps(noGodeps)
	parser_config.setParsePath(path)
	parser_config.setImportsOnly()

	data = {
		"type": "user_directory",
		"resource": os.path.abspath(path),
		"ipprefix": "."
	}

	try:
		data = ActFactory().bake("go-code-inspection").call(data)
	except Exception as e:
		logging.error(e)
		exit(1)

	prj_info = ProjectInfoBuilder().build()
	# TODO(jchaloup) catch exceptions, at least ValueError
	prj_info.construct(data[ARTEFACT_GOLANG_PROJECT_PACKAGES])

	occurrences = prj_info.getImportsOccurrence()
	main_occurrences = prj_info.getMainOccurrence()

	# ip used into devel packages
	if options.alloccurrences:
		ip_used = list(set(occurrences.keys() +  main_occurrences.keys()))
	else:
		ip_used = list(set(occurrences.keys()))

	decomposer = ImportPathsDecomposerBuilder().buildLocalDecomposer()
	# TODO(jchaloup) catch exceptions, at least ValueError
	decomposer.decompose(ip_used)
	classes = decomposer.classes()
	sorted_classes = sorted(classes.keys())

	# get max length of all imports
	max_len = 0
	for element in sorted_classes:
		if element == "Native":
			continue

		# class name starts with prefix => filter out
		if options.importpath != "" and element.startswith(options.importpath):
			continue

		gimports = []
		for gimport in classes[element]:
			if options.importpath != "" and gimport.startswith(options.importpath):
				continue
			gimports.append(gimport)

		for gimport in gimports:
			if options.showmain:
				if gimport not in main_occurrences:
					continue

			import_len = len(gimport)
			if import_len > max_len:
				max_len = import_len

	if options.spec and options.showoccurrence:
		print "# THIS IS NOT A VALID SPEC FORMAT"
		print "# COMMENTS HAS TO START AT THE BEGGINING OF A LINE"


	for element in sorted_classes:
		if not options.all and element == "Native":
			continue

		if not options.alloccurrences:
			one_class = []
			for gimport in classes[element]:
				# Assumption: dependencies of devel package
				# are free of deps of main packages
				one_class.append(gimport)

			classes[element] = sorted(one_class)

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
						if options.showoccurrence:
							if options.showmain:
								if gimport in main_occurrences:
									file_list = "(%s)" % ",".join(main_occurrences[gimport])
									if gimport in occurrences:
										file_list = "+" + file_list

									print "\t%s %s" % (gimport, file_list)
							else:
								print "\t%s (%s)" % (gimport, ", ".join(occurrences[gimport]))
						else:
							print "\t%s" % gimport
				continue

			# Translate non-native class into package name (if -d option)
			if options.pkgdb:
				name_generator = PackageNameGeneratorBuilder().buildWithLocalMapping()
				pkg_name = name_generator.generate(element).name()
				pkg_in_pkgdb = PkgDBClient().packageExists(pkg_name)
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
					if options.showoccurrence:
						if options.showmain:
							if gimport in main_occurrences:
								file_list = "(%s)" % ",".join(main_occurrences[gimport])
								if gimport in occurrences:
									file_list = "+" + file_list

								print "\t%s %s" % (gimport, file_list)
						else:
							print "\t%s (%s)" % (gimport, ", ".join(occurrences[gimport]))
					else:
						print "\t%s" % gimport
			continue

		# Spec file BR
		if options.spec:
			for gimport in sorted(classes[element]):
				if options.requires:
					if options.showoccurrence:
						import_len = len(gimport)
						print "Requires: golang(%s) %s# %s" % (gimport, (max_len - import_len)*" ", ", ".join(occurrences[gimport]))
					else:
						print "Requires: golang(%s)" % gimport
				else:
					if options.showoccurrence:
						import_len = len(gimport)
						print "BuildRequires: golang(%s) %s# %s" % (gimport, (max_len - import_len)*" ", ", ".join(occurrences[gimport]))
					else:
						print "BuildRequires: golang(%s)" % gimport
			continue

		# Just a list of all import paths
		for gimport in sorted(classes[element]):
			if options.showoccurrence:
				import_len = len(gimport)
				if options.showmain:
					if gimport in main_occurrences:
						file_list = "(%s)" % ",".join(main_occurrences[gimport])
						if gimport in occurrences:
							file_list = "+" + file_list
						print "\t%s %s %s" % (gimport, (max_len - import_len)*" ", file_list)
				else:
					print "\t%s %s(%s)" % (gimport, (max_len - import_len)*" ", ", ".join(occurrences[gimport]))
			else:
				print "\t%s" % gimport

