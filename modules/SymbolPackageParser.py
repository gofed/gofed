from xml.dom import minidom
from xml.dom.minidom import Node
from NativeImports import NativeImports
from Base import Base

class SymbolPackageParser(Base):

	def __init__(self, path, read_native_imports=True):
		self.path = path
		self.native_imports = []
		self.read_native_imports = read_native_imports
		self.ip_provides = []
		self.imports = []
		# pkg_name.xml
		self.pkg_name = ""
		# devel_name-V-R (N-V-R)
		self.devel_name = ""

	def setNativeImports(self, imports):
		self.native_imports = imports

	def readNativeImports(self):
		ni_obj = NativeImports()
		if not ni_obj.retrieve():
			self.err = ni_obj.getError()
			return False

		self.native_imports = ni_obj.getImports()
		return True

	def getProvides(self):
		return self.ip_provides

	def getImports(self):
		return self.imports

	def getPkgName(self):
		return self.pkg_name

	def getDevelName(self):
		return self.devel_name

	def parse(self):
		if self.read_native_imports:
			self.readNativeImports()

		try:	
			xmldoc = minidom.parse(self.path)
		except Exception, e:
			self.err = e
			return False

		prj_node = xmldoc.getElementsByTagName('project')
		if len(prj_node) != 1:
			self.err = "%s: missing project tag" % path
			return False

		pkg_nodes = prj_node[0].getElementsByTagName("packages")
		if len(pkg_nodes) != 1:
			self.err = "%s: missing project tag" % path
			return False

		pkg_nodes = pkg_nodes[0].getElementsByTagName("package")

		self.devel_name = self.path.split(".")[0]

		self.ip_provides = []
		self.ip_imports = []
		for pkg_node in pkg_nodes:
			if "importpath" not in pkg_node.attributes.keys():
				self.err = "%s: missing import path tag" % path
				return False

			self.ip_provides.append(str(pkg_node.attributes["importpath"].value))

		imports_nodes = prj_node[0].getElementsByTagName("imports")
		if len(imports_nodes) != 1:
			self.err = "%s: len(imports_nodes) != 1" % path
			return False

		import_nodes = imports_nodes[0].getElementsByTagName("import")
		for import_node in import_nodes:
			if "path" not in import_node.attributes.keys():
				continue

			ip = import_node.attributes["path"].value
			prefix = ip.split('/')[0]
			if prefix in self.native_imports:
				continue

			# does package imports itself?
			if ip in self.ip_provides:
				continue

			self.ip_imports.append(str(ip))

		# get NVR
		if "nvr" not in prj_node[0].attributes.keys():
			self.err = "%s: missing nvr attribute" % path
			return False

		# what package does this build comes from
		self.pkg = "-".join(prj_node[0].attributes["nvr"].value.split("-")[:-2])

		return True

