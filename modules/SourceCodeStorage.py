from Base import Base
from TarballStorage import TarballStorage
import os
from Utils import runCommand
import shutil

class SourceCodeStorage(Base):

	def __init__(self, storage_directory, verbose = False):
		self.storage_directory = storage_directory
		self.verbose = verbose
		self.storage = TarballStorage(self.storage_directory)

	def getDirectory(self, importpath, commit):
		tarball = self.storage.getTarball(importpath, commit)
		if tarball == "":
			return ""

		tarball_dir = "%s_dir" % tarball
		# extract tarball if not already
		if not os.path.exists(tarball_dir):
			# let's suppose all tarballs are tar.gz
			# tar xf archive.tar -C /target/directory --strip-components=1
			os.mkdir(tarball_dir)
			so, se, rc = runCommand("tar -xf %s -C %s --strip-components=1" % (tarball, tarball_dir))
			if rc != 0 or se != "":
				self.err = "Unable to extract tarball"
				print "Unable to extract tarball: %s" % se
				shutil.rmtree(tarball_dir)
				return ""		

		return tarball_dir
