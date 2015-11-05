from Base import Base
from GoSymbols import Dir2GoSymbolsParser, Xml2GoSymbolsParser
from Config import Config
import re

# Project can be represented by:
# 1) xml file
# 2) tarball/directory

class ProjectDecompositionGraphBuilder(Base):

	def __init__(self, parser_config):
		Base.__init__(self)
		self.parser_config = parser_config

		self.import_path_prefix = self.parser_config.getImportPathPrefix()
		self.skip_errors = self.parser_config.skipErrors()
		self.noGodeps = self.parser_config.getNoGodeps()
		# if set scan only some packages (and all direct/indirect imported local packages)
		self.partial = self.parser_config.isPartial()
		self.included_packages = self.parser_config.getPartial()
		self.marked_nodes = {}
		self.partial_nodes = {}

		self.api = None
		self.nodes = []
		self.edges = {}

	def loadPackageDefinitionMapping(self):
		path = Config().getPackageDefinitionMapping()
		with open(path, "r") as file:
			lines = file.read().split("\n")

		mapping = {}
		for line in lines:
			if len(line) == 0 or line[0] == "#":
				continue

			line = re.sub(r'[\t ]+', ' ', line).split(' ')
			mapping[line[0]] = line[1]

		return mapping

	def getNodes(self):
		return self.nodes

	def getEdges(self):
		return self.edges

	def getGraph(self):
		return (self.nodes, self.edges)

	def getSubpackageMembership(self):
		return {}

	def buildFromDirectory(self, directory):
		parser_config = self.parser_config
		parser_config.setParsePath(directory)
		self.api = Dir2GoSymbolsParser(parser_config)
		return self.build()

	def buildFromXml(self, xml_file):
		self.api = Xml2GoSymbolsParser(xml_file)

		return self.build()

	def mark_adjacent_nodes(self, node):
		if node not in self.edges:
			return

		for v in self.edges[node]:
			if not self.marked_nodes[v]:
				self.marked_nodes[v] = True
				self.mark_adjacent_nodes(v)

	def mark(self):
		"""
		1) Mark all nodes in include_packages
		2) Mark all nodes reachable from include_packages
		"""

		for node in self.nodes:
			self.marked_nodes[node] = False

		for node in self.included_packages:
			if node not in self.marked_nodes:
				print "ProjectDecompositionGraphBuilder: %s not found!!!" % node
				exit(1)

			self.marked_nodes[node] = True

		for node in self.included_packages:
			self.mark_adjacent_nodes(node)

		imported_packages = self.api.getPackageImports()
		package_definition_mapping = self.loadPackageDefinitionMapping()

		for node in self.marked_nodes:
			if self.marked_nodes[node]:
				if node == ".":
					if self.import_path_prefix in package_definition_mapping:
						ip = ".:" + package_definition_mapping[self.import_path_prefix]
					else:
						ip = ".:" + self.import_path_prefix.split("/")[-1]
				else:
					ip = "%s:%s" % (node, node.split("/")[-1])
				if ip not in imported_packages:
					print "Package %s not found. Maybe missing package definition mapping..." % ip
					exit(1)

				self.partial_nodes[node] = imported_packages[ip]

	def getPartial(self):
		return self.partial_nodes 

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

				if ip == "":
					ip = "."

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

		if self.partial:
			self.mark()

		return True
