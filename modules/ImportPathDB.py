import os
import re
from Utils import getScriptDir
from Config import Config
from xml.dom import minidom
from xml.dom.minidom import Node
from NativeImports import NativeImports
from Base import Base
from SymbolPackageParser import SymbolPackageParser
from lxml import etree

class ImportPathDBCache(Base):

	def __init__(self):
		self.ip_provides = {}
		self.ip_imports = {}
		self.devel_main_pkg = {}

	def addBuild(self, devel_name, provides, imports, main_pkg):
		if devel_name not in self.devel_main_pkg:
			self.ip_provides[devel_name] = provides
			self.ip_imports[devel_name] = imports
			self.devel_main_pkg[devel_name] = main_pkg

	def updateBuild(self, devel_name, provides, imports, main_pkg):
		self.ip_provides[devel_name] = provides
		self.ip_imports[devel_name] = imports
		self.devel_main_pkg[devel_name] = main_pkg

	def getDevelNames(self):
		return self.ip_provides.keys()

	def getProvides(self, devel_name):
		if devel_name in self.ip_provides:
			return self.ip_provides[devel_name]
		else:
			return []

	def getImports(self, devel_name):
		if devel_name in self.ip_imports:
			return self.ip_imports[devel_name]
		else:
			return []

	def getMainPkg(self, devel_name):
		if devel_name in self.devel_main_pkg:
			return self.devel_main_pkg[devel_name]
		else:
			return ""

	def load(self):
		path = Config().getGolangImPrPackages()
		xmldoc = None
		try:
			xmldoc = minidom.parse(path)
		except Exception, e:
			self.err = e
			return False

		cache_node = xmldoc.getElementsByTagName("cache")
		if len(cache_node) == 0:
			self.err = "<cache> tag missing"
			return False

		self.ip_provides = {}
		self.ip_imports = {}
		self.devel_main_pkg = {}

		for build in cache_node[0].getElementsByTagName("build"):
			attrs = build.attributes
			if 'name' not in attrs.keys():
				continue

			if 'package' not in attrs.keys():
				continue

			# get build name
			devel_name = str(attrs['name'].value)

			# get main pkg
			main_pkg = str(attrs['package'].value)

			# get a list of provides
			provides_node = build.getElementsByTagName("provides")
			if len(provides_node) == 0:
				continue

			provides = []
			for provide_node in provides_node[0].getElementsByTagName("provide"):
				if 'value' not in provide_node.attributes.keys():
					continue

				provides.append(str(provide_node.attributes['value'].value))

			# get a list of imports
			imports_node = build.getElementsByTagName("imports")
			if len(imports_node) == 0:
				continue

			imports = []
			for import_node in imports_node[0].getElementsByTagName("import"):
				if 'value' not in import_node.attributes.keys():
					continue

				imports.append(str(import_node.attributes['value'].value))

			self.ip_provides[devel_name] = provides
			self.ip_imports[devel_name] = imports
			self.devel_main_pkg[devel_name] = main_pkg
	
		return True

	def flush(self):
		cache_node = etree.Element("cache")
		for devel_name in self.devel_main_pkg.keys():
			build_node = etree.Element("build")
			build_node.set("name", devel_name)
			# main package
			build_node.set("package", self.devel_main_pkg[devel_name])

			# provides
			provides_node = etree.Element("provides")
			for provide in self.ip_provides[devel_name]:
				provide_node = etree.Element("provide")
				provide_node.set("value", provide)
				provides_node.append(provide_node)

			build_node.append(provides_node)

			# imports
			imports_node = etree.Element("imports")
			for ip_import in self.ip_imports[devel_name]:
				import_node = etree.Element("import")
				import_node.set("value", ip_import)
				imports_node.append(import_node)

			build_node.append(imports_node)
			cache_node.append(build_node)

		path = Config().getGolangImPrPackages()
		try:
			with open(path, 'w') as file:
				file.write(etree.tostring(cache_node, pretty_print=True))
		except IOError, e:
			self.err = "Unable to open %s: %s" % (path, e)
			return False

		return True


class ImportPathDB(Base):

	def __init__(self, cache=False):
		self.ip_provides = {}
		self.ip_imports = {}
		self.devel_main_pkg = {}
		self.warn = []
		self.cache=cache

	def getProvidedPaths(self):
		return self.ip_provides

	def getImportedPaths(self):
		return self.ip_imports

	def getDevelMainPkg(self):
		return self.devel_main_pkg

	def load(self):
		"""
		For each subpackage return all imported and provided import paths
		"""
		# one package can have more *.xml files
		self.ip_provides = {}
		self.ip_imports = {}
		self.pkg_devel_main_pkg = {}

		ni_obj = NativeImports()
		if not ni_obj.retrieve():
			self.err = ni_obj.getError()
			return False

		native_imports = ni_obj.getImports()

		golang_pkg_path = Config().getGolangPkgdb()

		symbol_files = []

		for dirName, subdirList, fileList in os.walk(golang_pkg_path):
			for fname in fileList:
				if not fname.endswith(".xml"):
					continue

				symbol_files.append("%s/%s" % (dirName,fname))

		ipdb_cache = ImportPathDBCache()
		if self.cache:
			if not ipdb_cache.load():
				self.err = ipdb_cache.getError()
				return False

			devel_names = ipdb_cache.getDevelNames()
			for name in devel_names:
				self.ip_provides[name] = ipdb_cache.getProvides(name)
				self.ip_imports[name] = ipdb_cache.getImports(name)
				# what package does this build comes from
				self.devel_main_pkg[name] = ipdb_cache.getMainPkg(name)

			return True

		for path in symbol_files:
			print path
			spp_obj = SymbolPackageParser(path,
					read_native_imports=False)

			spp_obj.setNativeImports(native_imports)
			if not spp_obj.parse():
				self.warn.append(spp_obj.getError())
				continue

			devel_name = spp_obj.getDevelName()

			self.ip_provides[devel_name] = spp_obj.getProvides()
			self.ip_imports[devel_name] = spp_obj.getImports()
				
			# what package does this build comes from
			self.devel_main_pkg[devel_name] = spp_obj.getPkgName()

			ipdb_cache.addBuild(devel_name, self.ip_provides[devel_name], self.ip_imports[devel_name], spp_obj.getPkgName())

		ipdb_cache.flush()

		return True

