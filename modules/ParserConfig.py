

class ParserConfig:

	def __init__(self):
		self.skip_errors = False
		self.noGodeps = []
		self.import_path_prefix = ""
		self.path = ""
		# if set scan only some packages (and all direct/indirect imported local packages)
		self.partial = False
		self.include_packages = []

		self.imports_only = False
		self.verbose = False

	def setSkipErrors(self):
		self.skip_errors = True

	def skipErrors(self):
		return self.skip_errors


	def setNoGodeps(self, dirs):
		self.noGodeps = dirs

	def hasNoGodeps(self):
		return self.noGodeps != []

	def getNoGodeps(self):
		return self.noGodeps	


	def setImportPathPrefix(self, prefix):
		self.import_path_prefix = prefix

	def getImportPathPrefix(self):
		return self.import_path_prefix


	def setParsePath(self, path):
		self.path = path

	def getParsePath(self):
		return self.path


	def setPartial(self, packages):
		self.partial = True
		self.include_packages = packages

	def isPartial(self):
		return self.partial

	def getPartial(self):
		return self.include_packages


	def setImportsOnly(self):
		self.imports_only = True

	def isImportsOnly(self):
		return self.imports_only


	def setVerbose(self):
		self.verbose = True

	def isVerbose(self):
		return self.verbose
