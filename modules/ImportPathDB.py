import os
import re
from Utils import getScriptDir
from Config import Config
from xml.dom import minidom
from xml.dom.minidom import Node
from NativeImports import NativeImports
from Base import Base
from SymbolPackageParser import SymbolPackageParser

class ImportPathDB(Base):

	def __init__(self):
		self.ip_provides = {}
		self.ip_imports = {}
		self.devel_main_pkg = {}
		self.warn = []

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

		return True

