from Base import Base
from ImportPath import ImportPath
from SpecParser import SpecParser
from SpecParser import Sources
from os import path
from ProjectInfo import ProjectInfo
import tempfile
import shutil
from Utils import runCommand
from Config import Config

#
# 1. URL tag: should be https://%{import_path} otherwise it can not be used
#             for package name check test
# 2. %{import_path}: must be present, it is an import path for the main devel
# 3. 1-1-1 rule: 1 package, 1 tarball, 1 devel. The rest is package specific.
#
# 4. basename(source0) has to be found in Sources file
# Package specific: decomposition of a devel subpackage into smaller subpackages
#                   back-compatibility devel subpackages
#                   various versions of a devel subpackage (check.in has v1 and v2)
#
# If I decompose a devel subpackage into smaller subpackages, how am I going to
# check a list of provides and [B]Rs? %global check_devel nil? Or check
# B[R] of what devel subpackage depends on (in case it depends on local subpackages)?
#
# TODO
# [  ] - describe %{devel_main} and %{devel_prefix} macros in documentation
# [  ] - sources is present only in repo, not before review request (skip the test)
# [  ] - add %{devel_clone} and %{clone_import_path} to check other devel subpackages
# [  ] - how to check decomposed devel subpackages? API breakage on a level of decomposed subpackages? Graph algorithms!!!
# [  ] - how to check debug_package macro? How to detect if the spec provides only sources? %build section is empty?

class GoLint(Base):

	def __init__(self, spec, sources, archive, verbose = False, stdout = True, noGodeps = []):
		Base.__init__(self)
		self.spec = spec
		self.sources = sources
		self.archive = archive
		self.verbose = verbose
		self.stdout = stdout
		self.test_results = []
		self.t_result = ""
		self.noGodeps = noGodeps

		self.err_number = 0
		self.warn_number = 0

		self.sp_obj = None
		self.src_obj = None
		self.prj_obj = None

	def getErrorCount(self):
		return self.err_number

	def getWarningCount(self):
		return self.warn_number

	def getTestResults(self):
		return self.test_results

	def printTResult(self, t_result):
		if type(t_result) == type([]):
			if self.stdout:
				print "\n".join(t_result)
			else:
				self.test_results += t_result
		else:
			if self.stdout:
				print t_result
			else:
				self.test_results.append(t_result)

	def test(self):
		# Parse spec file
		self.sp_obj = SpecParser(self.spec)
		if not self.sp_obj.parse():
			self.err = self.sp_obj.getError()
			return False

		# Parse sources file
		if self.sources != "":
			self.src_obj = Sources(self.sources)
			if not self.src_obj.parse():
				self.err = self.src_obj.getError()
				return False

		# Inspect tarball
		self.prj_obj = ProjectInfo(noGodeps = self.noGodeps)
		# create a temp directory
		dir = tempfile.mkdtemp()
		# extract tarball to the directory
		so, se, rc = runCommand("tar -xf %s --directory=%s" % (self.archive, dir))
		if rc != 0:
			self.err = se
			return False

		so, se, rc = runCommand("ls %s" % dir)
		if rc != 0:
			self.err = "Unable to archive's extracted folder"
			return False

		so = so.split('\n')[0]
		if not self.prj_obj.retrieve("%s/%s" % (dir, so), skip_errors = True):
			self.err = self.prj_obj.getError()
			return False

		shutil.rmtree(dir)

		tests = []

		# test package name
		tests.append(self.testPackageName)
		# test commit
		tests.append(self.testCommit)
		# test import path macros
		tests.append(self.testImportPathMacros)
		# test provider, provider_tld, ...
		tests.append(self.testRepositoryMacros)
		# test source0 macro
		tests.append(self.testSpecFileSource)
		# test devel subpackage
		tests.append(self.testDevel)

		for test in tests:
			if not test():
				self.printTResult(self.t_result)
			elif self.verbose:
				self.printTResult(self.t_result)

		return True

	def testPackageName(self):
		name = self.sp_obj.getTag('name')
		url = self.sp_obj.getTag('url')

		if name == "":
			self.t_result = "E: Missing name tag"
			self.err_number += 1
			return False

		if url == "":
			self.t_result = "E: Missing url tag"
			self.err_number += 1
			return False

		ip_obj = ImportPath(url)
		if not ip_obj.parse():
			self.err = ip_obj.getError()
			return False

		pkg_name = ip_obj.getPackageName()
		if pkg_name == '':
			self.t_result = "E: Uknown repo url"
			self.err_number += 1
			return False

		if pkg_name != name:
			self.t_result = "W: Incorrect package name %s, should be %s" % (name, pkg_name)
			self.warn_number += 1
			return False

		self.t_result = "I: Package name correct"
		return True

	def testCommit(self):
		commit_label = 'commit'
		commit = self.sp_obj.getMacro(commit_label)
		if commit == "":
			commit_label = 'rev'
			commit = self.sp_obj.getMacro(commit_label)

		if commit == "":
			self.t_result = "E: missing %global commit or rev"
			self.err_number += 1
			return False

		if commit_label == "commit":
			if self.sp_obj.getMacro("shortcommit") == "":
				self.t_result = "E: missing %global shortcommit"
				self.err_number += 1
				return False
			self.t_result = "I: commit and shortcommit macro"
		else:
			if self.sp_obj.getMacro("shortrev") == "":
				self.t_result = "E: missing %global shortrev"
				self.err_number += 1
				return False
			self.t_result = "I: rev and shortrev macro"

		return True

	def testImportPathMacros(self):
		devel_prefix = self.sp_obj.getMacro('devel_prefix')
		if devel_prefix == "":
			import_path = self.sp_obj.getMacro('import_path')
			ip_macro = "import_path"
		else:
			import_path = self.sp_obj.getMacro('%s_import_path' % devel_prefix)
			ip_macro = "%s_import_path" % devel_prefix

		if import_path == "":
			self.t_result = "E: Missing %%{%s} macro" % ip_macro
			self.err_number += 1
			return False

		self.t_result = "I: %s macro found" % ip_macro
		return True

	def testRepositoryMacros(self):
		provider = self.sp_obj.getMacro('provider')
		if provider == "":
			self.t_result = "E: Missing %{provider} macro"
			self.err_number += 1
			return False

		provider_tld = self.sp_obj.getMacro('provider_tld')
		if provider_tld == "":
			self.t_result = "E: Missing %{provider_tld} macro"
			self.err_number += 1
			return False

		repo = self.sp_obj.getMacro('repo')
		if repo == "":
			self.t_result = "E: Missing %{repo} macro"
			self.err_number += 1
			return False

		project = self.sp_obj.getMacro('project')
		if project == "":
			self.t_result = "E: Missing %{project} macro"
			self.err_number += 1
			return False

		self.t_result = "I: provider, provider_tld, repo and project macros found"
		return True

	def testSpecFileSource(self):
		source = self.sp_obj.getTag('source')
		if source == "":
			self.t_result = "E: Missing source tag"
			self.err_number += 1
			return False

		archive = path.basename(source)

		if self.sources != "":
			sources = self.src_obj.getFiles()

			if archive not in sources:
				self.t_result = "E: archive in source[0] tag not in sources file"
				self.err_number += 1
				return False

		if archive != self.archive:
			self.t_result = "E: sources[0]'s tarball != specified tarball: %s != %s" % (archive, self.archive)
			self.err_number += 1
			return False

		self.t_result = "I: %s archive found in sources" % archive
		return True

	def testDevel(self):
		# get provided and imported paths from tarball
		t_imported = self.prj_obj.getImportedPackages()
		t_provided = self.prj_obj.getProvidedPackages()
		devel_prefix = self.sp_obj.getMacro('devel_prefix')
		if devel_prefix == "":
			import_path = self.sp_obj.getMacro('import_path')
		else:
			import_path = self.sp_obj.getMacro('%s_import_path' % devel_prefix)

		t_imported = filter(lambda i: not i.startswith(import_path), t_imported)
		t_imported = map(lambda i: str("golang(%s)" % i), t_imported)

		skipped_provides_with_prefix = Config().getSkippedProvidesWithPrefix()

		for provide_prefix in skipped_provides_with_prefix:
			t_provided = filter(lambda i: not i.startswith(provide_prefix), t_provided)

		t_provided = map(lambda i: str("golang(%s/%s)" % (import_path, i)) if i != "." else str("golang(%s)" % import_path), t_provided)
		# get provides and [B]R from package section
		devel_obj = self.sp_obj.getDevelSubpackage()
		if devel_obj == None:
			self.t_result = "E: Unable to find devel subpackage"
			self.err_number += 1
			return False

		s_br = filter(lambda l: l != "golang", devel_obj.getBuildRequires())
		s_r = devel_obj.getRequires()
		s_provided = devel_obj.getProvides()

		# compare
		self.t_result = []
		# BR
		super_br = list(set(s_br) - set(t_imported) - set(['golang']))
		missing_br = list(set(t_imported) - set(s_br))
		for br in missing_br:
			self.t_result.append("W: Missing BuildRequires: %s" % br)
			self.warn_number += 1

		for br in super_br:
			self.t_result.append("W: Superfluous BuildRequires: %s" % br)
			self.warn_number += 1

		# R
		super_r = list(set(s_r) - set(t_imported) - set(['golang']))
		missing_r = list(set(t_imported) - set(s_r))
		for r in missing_r:
			self.t_result.append("W: Missing Requires: %s" % r)
			self.warn_number += 1

		for r in super_r:
			self.t_result.append("W: Superfluous Requires: %s" % r)
			self.warn_number += 1

		# Provides
		super_p = list(set(s_provided) - set(t_provided))
		missing_p = list(set(t_provided) - set(s_provided))
		for p in missing_p:
			self.t_result.append("W: Missing Provides: %s" % p)
			self.warn_number += 1

		for p in super_p:
			self.t_result.append("W: Superfluous Provides: %s" % p)
			self.warn_number += 1

		if self.t_result != []:
			return False

		self.t_result = "I: devel's provides checked"
		return True
