from RepositoryInfo import RepositoryInfo
from ProjectInfo import ProjectInfo
import os

class PackageInfo:
	"""
	Get basic information about project:
		imported packages
		provided packages
		tests
	"""
	def __init__(self, import_path, commit = "", noGodeps = []):
		self.import_path = import_path
		self.commit = commit
		self.noGodeps = noGodeps
		self.err = ""
		self.repository_info = None
		self.project_info = None
		self.archive_dir = ""
		self.repository_decoded = False
		self.name = ""

	def getError(self):
		return self.err

	def getName(self):
		return self.name

	def getRepositoryInfo(self):
		return self.repository_info

	def getProjectInfo(self):
		return self.project_info

	def decodeRepository(self):
		# get repository info
		self.repository_info = RepositoryInfo(self.import_path, self.commit)
		if not self.repository_info.retrieve():
			self.err = self.repository_info.getError()
			return False

		# package name
		ip_info = self.repository_info.getImportPathInfo()

		r_info = self.repository_info.getArchiveInfo()

		self.repository_decoded = True
		self.archive_dir = r_info.archive_dir
		self.name = ip_info.getPackageName()
		return True

	def decodeProject(self, working_directory = "."):
		if not self.repository_decoded:
			self.err = "RepositoryInfo not decoded"
			return False

		# get package info
		self.project_info = ProjectInfo(self.noGodeps)
		source_code_directory = "%s/%s" % (working_directory, self.archive_dir)
		if not os.path.exists(source_code_directory):
			self.err = "Source code directory %s does not exist." % source_code_directory
			self.err += "CWD: %s" % os.getcwd()
			return False

		if not self.project_info.retrieve(source_code_directory):
			self.err = self.project_info.getError()
			return False

	
		return True


