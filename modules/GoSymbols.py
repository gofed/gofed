#!/bin/python

###############################################################################
# ========exported symbols (package units)========
# 1) list all directories containing go files
# 2) for each file in each directory list all its symbols
# 3) merge symbols belonging to the same package
# 4) for each import path make a database of all symbols
# 5) create go2fed gosymbols script (--list, --importpath, --status)
#
# ========imported symbols (file units)========
# 1) for each file list all imports
# 2) for each file search for all used types, variables, constants, functions
# 3) 
#
# - if . imports are presented, it is not trivial to know from which package
# used symbols are imported. What I have to do is to:
#   a) check the package for all defined local functions, variables, constants
#      and types
#   b) from each . import, list all symbols. If symbols are not mutually
#      exclusive (this can change by any package  update), report error.
#   c) from each file list all symbols not found in a)
#   d) map symbols found in c) to symbols exported from all . imports
#
# Each day make a snapshot of all provided import paths and exported symbols.
# This will be used as a source for "used symbols" matching
#
###############################################################################
# Using GoSymbols scan will replace go2fed scan-imports as it has a list of all
# packages and all imports. Exported symbols gives more informations about what
# is provided. Local database format has to be replaced with a more expressive
# one. Using xml for that as it can be read as it is.
#
# Extracted json should be transformed into a better representation (some keys
# are redundant, some types can be described in a more simple way.
###############################################################################

import os
import sys
from Utils import runCommand, getScriptDir
import json
from lxml import etree

def getGoDirs(directory, test = False):
	go_dirs = []
	for dirName, subdirList, fileList in os.walk(directory):
		# does the dirName contains *.go files
		nogo = True
		for fname in fileList:
			# find any *.go file
			if test == False and fname.endswith(".go"):
				nogo = False
				break
			elif test == True and fname.endswith("_test.go"):
				nogo = False
				break

		if nogo:
			continue

		relative_path = os.path.relpath(dirName, directory)
		go_dirs.append(relative_path)

	return go_dirs	

def getGoFiles(directory):
	go_dirs = []
	for dirName, subdirList, fileList in os.walk(directory):
		# skip all directories with no file
		if fileList == []:
			continue

		go_files = []
		for fname in fileList:
			# find any *.go file
			# but skip all test files
#			if fname.endswith("_test.go"):
#				continue

			if fname.endswith(".go"):
				go_files.append(fname)

		# skipp all directories with no *.go file
		if go_files == []:
			continue

		relative_path = os.path.relpath(dirName, directory)
		go_dirs.append({
			'dir': relative_path,
			'files': go_files,
		})

	return go_dirs

def getGoSymbols(path, imports_only=False):
	script_dir = getScriptDir() + "/.."
	options = ""
	if imports_only:
		options = "-imports"

	so, se, rc = runCommand("%s/parseGo %s %s" % (script_dir, options, path))
	if rc != 0:
		return (1, se)

	return (0, so)

def mergeGoSymbols(jsons = []):
	"""
	Exported symbols for a given package does not have any prefix.
	So I can drop all import paths that are file specific and merge
	all symbols.
	Assuming all files in the given package has mutual exclusive symbols.
	"""
	# <siXy> imports are per file, exports are per package
	# on the highest level we have: pkgname, types, funcs, vars, imports.

	symbols = {}
	symbols["types"] = []
	symbols["funcs"] = []
	symbols["vars"]  = []
	for file_json in jsons:
		symbols["types"] += file_json["types"]
		symbols["funcs"] += file_json["funcs"]
		symbols["vars"]  += file_json["vars"]

	return symbols

def getSymbolsForImportPaths(go_dir, imports_only=False):
	bname = os.path.basename(go_dir)
	go_packages = {}
	ip_packages = {}
	ip_used = []
	for dir_info in getGoFiles(go_dir):
		#if sufix == ".":
		#	sufix = bname
		pkg_name = ""
		prefix = ""
		jsons = {}
		for go_file in dir_info['files']:
			go_file_json = {}
			err, output = getGoSymbols("%s/%s/%s" % 
				(go_dir, dir_info['dir'], go_file), imports_only)
			if err != 0:
				return "Error parsing %s: %s" % ("%s/%s" % (dir_info['dir'], go_file), output), {}, {}, {}
			else:
				#print go_file
				go_file_json = json.loads(output)

			for path in go_file_json["imports"]:
				if path["path"] not in ip_used:
					ip_used.append(path["path"])

			# don't check test files, read their import paths only
			if go_file.endswith("_test.go"):
				continue

			pname = go_file_json["pkgname"]
			# skip all main packages
			if pname == "main":
				continue

			if pkg_name != "" and pkg_name != pname:
				return "Error: directory %s contains defines of more packages, i.e. %s" % (dir_info['dir'], pkg_name), {}, {}, {}

			pkg_name = pname

			# build can contain two different prefixes
			# but with the same package name.
			prefix = dir_info["dir"] + ":" + pkg_name
			if prefix not in jsons:
				jsons[prefix] = [go_file_json]
			else:
				jsons[prefix].append(go_file_json)

		#print dir_info["dir"]
		#print dir_info['files']
		#print "#%s#" % pkg_name
		if prefix in jsons:
			go_packages[prefix] = mergeGoSymbols(jsons[prefix])
			ip_packages[prefix] = dir_info["dir"]

	return "", ip_packages, go_packages, ip_used

###############################################################################
# XML inner data representation
# <package path="code.google.com/p/gomock/gomock">
# 	<importList>
#		<import>fmt</import>
#		<import>reflect</import>
#		<import>strings</import>
#	</importList>
#	<typeList>
#		<type type="struct" name="Call">
#			<field name="t" type="ident" def="TestReporter" />
#			<field name="receiver" type="interface" />
#				
#			</field>
#			<field name="method" type="ident" def="string" />
#			<field name="args" type="array">
#				<type type="Matcher" />
#			</field>
#			<field name="rets" type="interface" />
#			<field name="preReqs" type="array">
#				<type type="pointer">
#					<type type="ident" def="Call" />
#				</type>
#			</field>
#			<field name="minCalls" type="ident" def="int" />
#			<field name="maxCalls" type="ident" def="int" />
#			<field name="numCalls" type="ident" def="int" />
#			<field name="doFunc" type="selector">
#				<prefix value="reflect" />
#				<type type="ident" def="Value" />
#			</field>
#			<field name="setArgs" type="map">
#				<keytype type="ident" def="int" />
#				<valuetype type="selector">
#					<prefix value="reflect" />
#					<type type="ident" def="Value" />
#				</valuetype>
#			</field>
#		</type>
#	</typeList>
# </package>

TYPE_IDENT = "ident"
TYPE_ARRAY = "array"
TYPE_SLICE = "slice"
TYPE_INTERFACE = "interface"
TYPE_POINTER = "pointer"
TYPE_SELECTOR = "selector"
TYPE_STRUCT = "struct"
TYPE_METHOD = "method"
TYPE_FUNC = "func"
TYPE_ELLIPSIS = "ellipsis"
TYPE_MAP = "map"
TYPE_CHANNEL = "channel"
TYPE_PARENTHESIS = "parenthesis"

class PackageToXml:

	def typeToXML(self, type_def, elm_name = "type"):
		self.level += 1
		#print "LEVEL: %s, %s" % (self.level, type_def["type"])
		#print type_def
		node = etree.Element(elm_name)
		if self.level == 1:
			node.set("name", type_def["name"])

		type_name = type_def["type"]
		#print type_name

		if type_name == TYPE_IDENT:
			node.set("type", "ident")
			if type(type_def["def"]) == type({}):
				err, t_def = self.typeToXML(type_def["def"])
				if err != "":
					return err, None

				node.append(t_def)
			else:
				node.set("def", type_def["def"])

		elif type_name == TYPE_INTERFACE:
			node.set("type", "interface")
			for method in type_def["def"]:
				err, method_node = self.typeToXML(method, "method")
				if err != "":
					return err, None

				method_node.set("name", method["name"])
				node.append(method_node)

		elif type_name == TYPE_POINTER:
			node.set("type", "pointer")
			err, t_def = self.typeToXML(type_def["def"])
			if err != "":
				return err, None

			node.append(t_def)

		elif type_name == TYPE_ELLIPSIS:
			node.set("type", "ellipsis")
			err, elt_node = self.typeToXML(type_def["elt"])
			if err != "":
				return err, None

			node.append(elt_node)

		elif type_name == TYPE_CHANNEL:
			node.set("type", "chan")
			if "dir" not in type_def:
				node.set("dir", type_def["def"]["dir"])
				err, val_node = self.typeToXML(type_def["def"]["value"])
			else:
				node.set("dir", type_def["dir"])
				err, val_node = self.typeToXML(type_def["value"])

			if err != "":
				return err, None

			node.append(val_node)

		# <type name="args" type="slice">
		# 	<type type="ident" def="Matcher" />                         
		# </type>
		elif type_name == TYPE_SLICE:
			node.set("type", "slice")
			err, t_def = self.typeToXML(type_def["elmtype"], "elmtype")
			if err != "":
				return err, None

			node.append(t_def)

		elif type_name == TYPE_ARRAY:
			node.set("type", "array")
			err, t_def = self.typeToXML(type_def["elmtype"], "elmtype")
			if err != "":
				return err, None

			node.append(t_def)

		elif type_name == TYPE_PARENTHESIS:
			node.set("type", "parenthesis")
			err, t_def = self.typeToXML(type_def["def"])
			if err != "":
				return err, None

			node.append(t_def)
		
		elif type_name == TYPE_MAP:
			node.set("type", "map")
			err, t_def = self.typeToXML(type_def["def"]["keytype"], "keytype")
			if err != "":
				return err, None

			node.append(t_def)

			err, t_def = self.typeToXML(type_def["def"]["valuetype"], "valtype")
			if err != "":
				return err, None

			node.append(t_def)

		# <valuetype type="selector">
		#	<prefix value="reflect" />
		#	<type type="ident" def="Value" />
		# </valuetype>
		elif type_name == TYPE_SELECTOR:
			node.set("type", "selector")
			prefix_node = etree.Element("prefix")

			prefix = ""
			item = ""
			if "prefix" not in type_def:
				prefix = type_def["def"]["prefix"]["def"]
				item   = type_def["def"]["item"]
			else:
				prefix = type_def["prefix"]["def"]
				item   = type_def["item"]

			prefix_node.set("value", prefix)
			node.append(prefix_node)
			item_node = etree.Element("item")
			item_node.set("value", item)
			node.append(item_node)
	
		elif type_name == TYPE_METHOD:
			params_node = etree.Element("paramsList")
			for item in type_def["def"]["params"]:
				err, t_def = self.typeToXML(item)
				if err != "":
					return err, None

				params_node.append(t_def)

			results_node = etree.Element("resultsList")
			for item in type_def["def"]["results"]:
				err, t_def = self.typeToXML(item)
				if err != "":
					return err, None

				results_node.append(t_def)

			node.append(params_node)
			node.append(results_node)

		elif type_name == TYPE_FUNC:
			# receiver is defined on file scope
			node.set("type", "func")
			params_node = etree.Element("paramsList")

			params = []
			results = []
			if "params" not in type_def:
				params = type_def["def"]["params"]
				results = type_def["def"]["results"]
			else:
				params = type_def["params"]
				results = type_def["results"]

			for item in params:
				err, t_def = self.typeToXML(item)
				if err != "":
					return err, None

				params_node.append(t_def)

			results_node = etree.Element("resultsList")
			for item in results:
				err, t_def = self.typeToXML(item)
				if err != "":
					return err, None

				results_node.append(t_def)

			node.append(params_node)
			node.append(results_node)

		elif type_name == TYPE_STRUCT:
			ret = self.structToXML(type_def)
			self.level -= 1
			return ret

		else:
			return "Type %s not yet implemented" % type_name, None

		self.level -= 1
		return "", node

	def structToXML(self, str_def):
		root = etree.Element("type")
		root.set("type", "struct")
		root.set("name", str_def["name"])
		for field in str_def["def"]:
			# <field name="t" type="ident" def="TestReporter" />
			err, node = self.typeToXML(field["def"], "field")
			if err != "":
				return err, None

			node.set("name", field["name"])	
			root.append(node)

		return "", root

	def funcToXML(self, func_def):
		self.level += 1
		#print "LEVEL: %s, %s" % (self.level, "func")
		root = etree.Element("function")
		root.set("name", func_def["name"])

		list_node = etree.Element("recvList")
		for item in func_def["def"]["recv"]:
			err, type_def = self.typeToXML(item)
			if err != "":
				return err, None

			list_node.append(type_def)

		root.append(list_node)

		list_node = etree.Element("paramsList")
		for item in func_def["def"]["params"]:
			err, type_def = self.typeToXML(item)
			if err != "":
				return err, None

			list_node.append(type_def)

		root.append(list_node)

		list_node = etree.Element("returnsList")
		for item in func_def["def"]["returns"]:
			err, type_def = self.typeToXML(item)
			if err != "":
				return err, None

			list_node.append(type_def)

		root.append(list_node)

		self.level -= 1
		return "", root

	def typesToXML(self, types):
		node = etree.Element("types")
		for item in types:
			err, type_def = self.typeToXML(item)
			if err != "":
				return err, None

			node.append(type_def)
		return "", node

	def functionsToXML(self, funcs):		
		node = etree.Element("functions")
		for item in funcs:
			err, type_def = self.funcToXML(item)
			if err != "":
				return err, None

			node.append(type_def)
		return "", node

	def __init__(self, symbols, import_path, imports=True):
		self.err = ""
		self.level = 0
		self.root = etree.Element("package")
		self.root.set("importpath", import_path)
		#print "IMPORTPATH: %s" % import_path

		self.err, types_node = self.typesToXML(symbols["types"])
		if self.err != "":
			return

		self.root.append(types_node)

		self.err, functions_node = self.functionsToXML(symbols["funcs"])
		if self.err != "":
			return

		self.root.append(functions_node)

		names_node = etree.Element("names")
		for item in symbols["vars"]:
			node = etree.Element("name")
			node.set("value", item)
			names_node.append(node)

		self.root.append(names_node)

		if imports:
			imports_node = etree.Element("imports")
			for item in symbols["imports"]:
				node = etree.Element("import")
				node.set("name", item["name"])
				node.set("path", item["path"])
				imports_node.append(node)

			self.root.append(imports_node)

	def getStatus(self):
		return self.err == ""

	def getError(self):
		return self.err

	def getPackage(self):
		return self.root

	def __str__(self):
		if self.err == "":
			return etree.tostring(self.root, pretty_print=True)
		else:
			return ""

class ProjectToXml:

	def __init__(self, url, go_dir, nvr = ""):
		"""
		url	prefix used for import paths
		go_dir	root directory containing go source codes
		"""

		self.err, ip, symbols, ip_used = getSymbolsForImportPaths(go_dir)
		if self.err != "":
			return

		self.root = etree.Element("project")
		self.root.set("url", url)
		self.root.set("commit", "commit")
		self.root.set("nvr", nvr)

		packages_node = etree.Element("packages")
		for prefix in ip:
			full_import_path = "%s/%s" % (url, ip[prefix])
			if url == "":
				full_import_path = ip[prefix]

			obj = PackageToXml(symbols[prefix], full_import_path, imports=False)
			if not obj.getStatus():
				self.err = obj.getError()
				return

			packages_node.append(obj.getPackage())

		self.root.append(packages_node)

		# add imports
		imports_node = etree.Element("imports")
		for path in ip_used:
			node = etree.Element("import")
			node.set("path", path)
			imports_node.append(node)

		self.root.append(imports_node)

	def getStatus(self):
		return self.err == ""

	def __str__(self):
		if self.err == "":
			return etree.tostring(self.root, pretty_print=True, xml_declaration=True)
		else:
			return ""

	def getError(self):
		return self.err

