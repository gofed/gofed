import os
import re
from Utils import getScriptDir
from Config import Config
from xml.dom import minidom
from xml.dom.minidom import Node

GOLANG_IMPORTS = "data/golang.imports"
GOLANG_PKG_DB = "data/pkgdb"
script_dir = getScriptDir() + "/.."

def getNativeImports():
	script_dir = getScriptDir() + "/.."
	with open('%s/%s' % (script_dir, GOLANG_IMPORTS), 'r') as file:
                content = file.read()
		return content.split('\n')

def loadImportPathDb():
	"""
	For each subpackage return all imported and provided import paths
	"""
	# one package can have more *.xml files
	ip_provides = {}
	ip_imports = {}
	pkg_devel_main_pkg = {}

	native_imports = getNativeImports()

	for dirName, subdirList, fileList in os.walk("%s/%s" % (script_dir, GOLANG_PKG_DB)):
		for fname in fileList:
			if not fname.endswith(".xml"):
				continue

			xmldoc = minidom.parse("%s/%s" % (dirName,fname))
			prj_node = xmldoc.getElementsByTagName('project')
			if len(prj_node) != 1:
				continue

			pkg_nodes = prj_node[0].getElementsByTagName("packages")
			if len(pkg_nodes) != 1:
				continue

			pkg_nodes = pkg_nodes[0].getElementsByTagName("package")

			devel_name = fname.split(".")[0]

			ip_provides[devel_name] = []
			ip_imports[devel_name] = []
			for pkg_node in pkg_nodes:
				if "importpath" not in pkg_node.attributes.keys():
					continue

				ip_provides[devel_name].append(str(pkg_node.attributes["importpath"].value))

			imports_nodes = prj_node[0].getElementsByTagName("imports")
			if len(imports_nodes) != 1:
				continue

			import_nodes = imports_nodes[0].getElementsByTagName("import")
			for import_node in import_nodes:
				if "path" not in import_node.attributes.keys():
					continue

				ip = import_node.attributes["path"].value
				prefix = ip.split('/')[0]
				if prefix in native_imports:
					continue

				# does package imports itself?
				if ip in ip_provides[devel_name]:
					continue

				ip_imports[devel_name].append(str(ip))

			# get NVR
			if "nvr" not in prj_node[0].attributes.keys():
				continue

			pkg = "-".join(prj_node[0].attributes["nvr"].value.split("-")[:-2])
			pkg_devel_main_pkg[devel_name] = str(pkg)

		return ip_provides, ip_imports, pkg_devel_main_pkg

def getDevelImportedPaths():
	_, ip_i, _ = loadImportPathDb()
	return ip_i

def getDevelProvidedPaths():
	ip_p, _, _ = loadImportPathDb()
	return ip_p

