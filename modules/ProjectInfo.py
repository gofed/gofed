from modules.GoSymbols import getSymbolsForImportPaths
from modules.ImportPaths import decomposeImports
from glob import glob
from os import path

class ProjectInfo:

	def __init__(self):
		self.err = ""
		self.imported_packages = []
		self.provided_packages = []
		self.docs = []

	def getError(self):
		return self.err

	def getImportedPackages(self):
		return self.imported_packages

	def getProvidedPackages(self):
		return self.provided_packages

	def getTestDirectories(self):
		return self.test_directories

	def getDocs(self):
		return self.docs

	def _getDocFiles(self, archive_directory):
		docs = []

		for doc in glob( path.join(archive_directory, '*.md') ):
			docs.append(path.basename(doc))

		for doc in ['Readme', 'README', 'LICENSE', 'AUTHORS', 'COPYING']:
			if path.exists("%s/%s" % (archive_directory, doc)):
				docs.append(doc)

		return docs

	def retrieve(self, directory, skip_errors = False):
		"""
		Retrieve information about project from directory
		"""
		# directory exists?
		if not path.exists(directory):
			self.err = "Directory %s does not exist" % directory
			return False

		err, packages, _, ip_used, tests = getSymbolsForImportPaths(directory, skip_errors = skip_errors)
                if err != "":
			self.err = err
			return False

                ips_imported = []
		ips_provided = []

		# imported paths
		classes = decomposeImports(ip_used)
	        sorted_classes = sorted(classes.keys())

		for ip_class in sorted_classes:
			if ip_class == "Native":
				continue

			for ip in classes[ip_class]:
				self.imported_packages.append(ip)

		# provided paths
		for pkg in packages:
			self.provided_packages.append(packages[pkg])

		# project documentation
		self.docs = self._getDocFiles(directory)

		self.imported_packages = sorted(self.imported_packages)
		self.provided_packages = sorted(self.provided_packages)
		self.test_directories = sorted(tests)

		return True

