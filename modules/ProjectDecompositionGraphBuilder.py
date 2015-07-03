from Base import Base
from GoSymbols import Dir2GoSymbolsParser, Xml2GoSymbolsParser

# Project can be represented by:
# 1) xml file
# 2) tarball/directory

class ProjectDecompositionGraphBuilder(Base):

	def __init__(self, import_path_prefix, skip_errors=False, noGodeps=[]):
		Base.__init__(self)
		self.import_path_prefix = import_path_prefix
		self.skip_errors = skip_errors
		self.noGodeps = noGodeps
		self.api = None
		self.nodes = []
		self.edges = {}

	def getNodes(self):
		return self.nodes

	def getEdges(self):
		return self.edges

	def getGraph(self):
		return (self.nodes, self.edges)

	def getSubpackageMembership(self):
		return {}

	def buildFromDirectory(self, directory):
		self.api = Dir2GoSymbolsParser(directory, skip_errors=self.skip_errors, noGodeps=self.noGodeps)
		return self.build()

	def buildFromXml(self, xml_file):
		self.api = Xml2GoSymbolsParser(xml_file)

		return self.build()

	def build(self):
		if not self.api.extract():
			self.err = self.api.getError()
			return False

		package_imports = self.api.getPackageImports()
		ip_prefix_len = len(self.import_path_prefix)

		for pkg in package_imports:
			package_name = pkg.split(":")[0]
			self.nodes.append(package_name)
			self.edges[package_name] = []

			for ip in package_imports[pkg]:
				# skip all imports not importing project's packages
				if not ip.startswith(self.import_path_prefix):
					continue

				# remove prefix from import path
				ip = ip[ip_prefix_len:]
				if ip != "/":
					ip = ip[1:]

				# skip all packages in noGodeps
				skip = False
				for nodir in self.noGodeps:
					if ip.startswith(nodir):
						skip = True
						continue
				if skip:
					continue

				# keep the rest
				self.edges[package_name].append(ip)
				self.nodes.append(ip)

			self.edges[package_name] = sorted(self.edges[package_name])

		self.nodes = list(set(self.nodes))
		return True
