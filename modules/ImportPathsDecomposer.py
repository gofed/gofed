from ImportPath import ImportPath
from Config import Config
from NativeImports import NativeImports

class ImportPathsDecomposer:

	def __init__(self, imports):
		self.warn = []
		self.err = ""
		self.classes = {}
		self.imports = imports

	def getWarning(self):
		return "\n".join(self.warn)

	def getError(self):
		return "\n".join(self.err)

	def getClasses(self):
		return self.classes

	def decompose(self):
		ni_obj = NativeImports()
		if not ni_obj.retrieve():
			self.err = ni_obj.getError()
			return False

		native = ni_obj.getImports()

		for gimport in self.imports:
			prefix = gimport.split('/')[0]
			if prefix in native:
				key = "Native"
			else:
				ip_obj = ImportPath(gimport)
				if not ip_obj.parse():
					self.warn.append(ip_obj.getError())
					key = "Unknown"
				else:
					key = ip_obj.getPrefix()

			if key not in self.classes:
				self.classes[key] = [gimport]
			else:
				self.classes[key].append(gimport)

		return True
