from Utils import getScriptDir
from ImportPath import ImportPath

GOLANG_IMPORTS = "data/golang.imports"
script_dir = getScriptDir() + "/.."

class ImportPathsDecomposer:

	def __init__(self, imports):
		self.warn = []
		self.classes = {}
		self.imports = imports

	def getWarning(self):
		return "\n".join(self.warn)

	def getNativeImports(self):
		script_dir = getScriptDir() + "/.."
		with open('%s/%s' % (script_dir, GOLANG_IMPORTS), 'r') as file:
	                content = file.read()
			return content.split('\n')

	def getClasses(self):
		return self.classes

	def decompose(self):
		native = self.getNativeImports()
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

