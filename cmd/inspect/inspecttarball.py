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

import os
import sys
import optparse
from gofed.modules.Config import Config

import logging
from gofedinfra.system.core.factory.actfactory import ActFactory
from gofedlib.go.projectinfobuilder import ProjectInfoBuilder
from gofedinfra.system.artefacts.artefacts import ARTEFACT_GOLANG_PROJECT_PACKAGES

from cmdsignature.parser import CmdSignatureParser
from gofedlib.utils import getScriptDir

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/inspecttarball.yml" % (cur_dir)

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	path = "."
	if len(args) == 0 or args[0] == "":
		path = args[0]

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

	if options.provides:
		skipped_provides_with_prefix = Config().getSkippedProvidesWithPrefix()

		for ip in sorted(prj_info.getProvidedPackages()):
			skip = False
			for prefix in skipped_provides_with_prefix:
				if ip.startswith(prefix):
					skip = True
					break

			if skip:
				continue

			# skip all provided packages with /internal/ keyword
			if "internal" in ip.split("/"):
				continue

			if options.spec != False:
				evr_string = "%{version}-%{release}"
				if options.epoch:
					evr_string = "%{epoch}:" + evr_string

				if ip != ".":
					print "Provides: golang(%%{import_path}/%s) = %s" % (ip, evr_string)
				else:
					print "Provides: golang(%%{import_path}) = %s" % (evr_string)
			elif options.prefix != "":
				if ip != ".":
					print "%s/%s" % (options.prefix, ip)
				else:
					print options.prefix
			else:
				print ip

	elif options.test:
		for dir in prj_info.getTestDirectories():
			if options.spec != False:
				if dir != ".":
					print "go test %%{import_path}/%s" % dir
				else:
					print "go test %{import_path}"
			else:
				print dir

	elif options.dirs:
		files = prj_info.getProvidedPackages() + prj_info.getTestDirectories()
		if options.mainpackages:
			files = files + prj_info.getMainPackages()

		dirs = map(lambda l: l.split("/")[0], files)
		dirs = sorted(list(set(dirs)))

		for dir in dirs:
			print dir
	elif options.mainpackages:
		for pkg in sorted(prj_info.getMainPackages()):
			print pkg
	else:
		print "Missing options. See command's help."
