from Base import Base
from RepositoryInfo import RepositoryInfo
import os
from Utils import runCommand


class TarballStorage(Base):

	def __init__(self, tarball_directory, verbose = False):
		self.tarball_directory = tarball_directory
		self.verbose = verbose

	def getTarball(self, importpath, commit):
		"""
		Search for a tarball in tarball directory.
		If it does not exist, download the tarball.

		TODO: Create a DirectoryStorage on top of TarballStorage?
		1) extract the archive to 
		2) rename its directory to TARBALLSIGNATURE_DIR
		3) return TARBALLSIGNATURE_DIR
		"""
		# tarball directory must exist
		if not os.path.exists(self.tarball_directory):
			self.err = "Tarball directory %s does not exist" % self.tarball_directory
			return ""

		ri = RepositoryInfo(importpath, commit)
		if not ri.retrieve():
			self.err = ri.getError()
			return ""

		# tarball exists?
		tarball_path = "%s/%s" % (self.tarball_directory, ri.getSignature())
		if not os.path.exists(tarball_path):
			ai = ri.getArchiveInfo()
			if self.verbose:
				print "Downloading %s ..." % ai.archive_url
			# download tarball
			so, se, rc = runCommand("wget -nv %s --no-check-certificate -O %s" % (ai.archive_url, tarball_path))
			if rc != 0:
				print "Unable to download tarball:\n%s" % (se)
				return ""

		return tarball_path
