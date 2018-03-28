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
from gofedlib.utils import GREEN, RED, ENDC
from gofed.modules.Utils import FormatedPrint
from gofed.modules.Config import Config

from gofedlib.go.importpath.decomposerbuilder import ImportPathsDecomposerBuilder
from gofedlib.go.projectinfobuilder import ProjectInfoBuilder
from gofedlib.distribution.clients.pkgdb.client import PkgDBClient
from gofedinfra.system.artefacts.artefacts import ARTEFACT_GOLANG_PROJECT_PACKAGES
from gofedlib.distribution.packagenamegeneratorbuilder import PackageNameGeneratorBuilder

import logging

from cmdsignature.parser import CmdSignatureParser
from gofedlib.utils import getScriptDir

from infra.system.workers import Worker
from infra.system.plugins.simplefilestorage.storagereader import StorageReader
from gofedlib.providers.providerbuilder import ProviderBuilder

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/%s.yml" % (cur_dir, os.path.basename(__file__).split(".")[0])

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	# TODO(jchaloup): finish the flag handeling
	#parser.add_option(
	#    "", "", "--include-tests", dest="includetests", action = "store_true", default = False,
	#    help = "Include dependencies for test too"
	#)

	if options.verbose:
		logging.basicConfig(level=logging.WARNING)
	else:
		logging.basicConfig(level=logging.ERROR)

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

	Worker("localgocodeinspection").setPayload({
		"directory": os.path.abspath(path),
	}).do()

	try:
		golang_project_packages_artefact = StorageReader().retrieve({
			"artefact": ARTEFACT_GOLANG_PROJECT_PACKAGES,
			"repository": ProviderBuilder().buildUpstreamWithLocalMapping().parse("github.com/local/local").signature(),
			"commit": "local",
			"ipprefix": "github.com/local/local",
		})
	except KeyError as err:
		logging.error(err)
		exit(1)

	prj_info = ProjectInfoBuilder().build()
	# TODO(jchaloup) catch exceptions, at least ValueError
	prj_info.construct(golang_project_packages_artefact)

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
