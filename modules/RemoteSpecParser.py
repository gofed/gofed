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

###################################################################
# TODO:
# [  ] - detect more import paths/sources in spec file?
# [  ] - detect from %files every build, analyze its content (downloading it from koji by detecting its name
#        from spec file => no koji latest-builds, which packages/builds are no arch, which are arch specific (el6 beast)
# [  ] - all provides of source code import must in a form golang(import_path/...)
# [  ] - what files/provides are optional, which should not be in provides (test files, example, ...)
# [  ] - golang imports of examples are optional
###################################################################

import tempfile
from Utils import runCommand
from SpecParser import SpecParser
from Base import Base

class RemoteSpecParser(Base):

	def __init__(self, branch, package):
		Base.__init__(self)
		self.branch = branch
		self.package = package
		self.sp_obj = None

	def parse(self):
		f = tempfile.NamedTemporaryFile(delete=True)
		cmd_str = "curl http://pkgs.fedoraproject.org/cgit/rpms/%s.git/plain/%s.spec > %s"
		runCommand(cmd_str % (self.package, self.package, f.name))
		self.sp_obj = SpecParser(f.name)
		if not self.sp_obj.parse():
			self.err = self.sp_obj.getError()
			f.close()
			return False

		f.close()
		return True

	def getProvides(self):
		"""Fetch a spec file from pkgdb and get provides from all its [sub]packages"""
		if self.sp_obj == None:
			return {}

		return self.sp_obj.getProvides()

	def getPackageCommits(self):
		if self.sp_obj == None:
			return ""

		return self.sp_obj.getMacro("commit")

	def getPkgURL(self):
		if self.sp_obj == None:
			return ""

		return self.sp_obj.getTag("url")

