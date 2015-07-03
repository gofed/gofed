import os
import json
import sys
from Utils import getScriptDir, runCommand

class GoSymbolsExtractor:

	def __init__(self, directory, imports_only=False, noGodeps=[], skip_errors=False):
		self.directory = directory
		self.err = ""
		self.imports_only = imports_only
		self.noGodeps = noGodeps
		self.skip_errors = skip_errors

		self.symbols = []
		self.symbols_position = {}
		# list of packages imported for each project's package
		self.package_imports = {}
		# list of packages imported in entire project
		self.imported_packages = []
		self.test_directories = []


	def getError(self):
		return self.err

	def getSymbols(self):
		return self.symbols

	def getSymbolsPosition(self):
		return self.symbols_position

	def getPackageImports(self):
		return self.package_imports

	def getImportedPackages(self):
		return self.imported_packages

	def getTestDirectories(self):
		return self.test_directories

	def getGoFiles(self, directory):
		go_dirs = []
		for dirName, subdirList, fileList in os.walk(directory):
			# skip all directories with no file
			if fileList == []:
				continue

			go_files = []
			for fname in fileList:
				# find any *.go file
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

	def getGoSymbols(self, path, imports_only=False):
		script_dir = getScriptDir() + "/.."
		options = ""
		if imports_only:
			options = "-imports"

		so, se, rc = runCommand("%s/parseGo %s %s" % (script_dir, options, path))
		if rc != 0:
			return (1, se)

		return (0, so)

	def mergeGoSymbols(self, jsons = []):
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

	def extract(self):
		"""

		"""
		bname = os.path.basename(self.directory)
		go_packages = {}
		ip_packages = {}
		test_directories = []
		ip_used = []
		package_imports = {}

		for dir_info in self.getGoFiles(self.directory):
			#if sufix == ".":
			#	sufix = bname
			pkg_name = ""
			prefix = ""
			jsons = {}
			if self.noGodeps != []:
				skip = False
				path_components = dir_info['dir'].split("/")
				for nodir in self.noGodeps:
					parts = nodir.split(":")
					name = parts[0]
					# empty means all elements
					max_depth = len(path_components)
					if len(parts) == 2 and parts[1].isdigit():
						max_depth = int(parts[1])

					if name in path_components[0:max_depth]:
						skip = True
						break
				if skip:
					continue

			for go_file in dir_info['files']:
				go_file_json = {}
				err, output = self.getGoSymbols("%s/%s/%s" % 
					(self.directory, dir_info['dir'], go_file), self.imports_only)
				if err != 0:
					if self.skip_errors:
						continue
					else:
						self.err = "Error parsing %s: %s" % ("%s/%s" % (dir_info['dir'], go_file), output)
						return False
				else:
					#print go_file
					go_file_json = json.loads(output)

				for path in go_file_json["imports"]:
					# filter out all import paths starting with ./
					if path["path"].startswith("./"):
						continue

					# filter out all .. import paths
					if path["path"] == "..":
						continue

					if path["path"] in ip_used:
						continue

					ip_used.append(path["path"])

				# don't check test files, read their import paths only
				if go_file.endswith("_test.go"):
					test_directories.append(dir_info['dir'])
					continue

				pname = go_file_json["pkgname"]
				# skip all main packages
				if pname == "main":
					continue

				if (pkg_name != "" and pkg_name != pname):
					err_msg = "Error: directory %s contains definition of more packages, i.e. %s" % (dir_info['dir'], pname)
					if self.skip_errors:
						sys.stderr.write("%s\n" % err_msg)
						continue
					self.err = err_msg
					return False

				if pname != os.path.basename(dir_info['dir']):
					err_msg = "Error: directory %s contains definition of different package, i.e. %s" % (dir_info['dir'], pname)
					if self.skip_errors:
						sys.stderr.write("%s\n" % err_msg)
						continue
					self.err = err_msg
					return False

				pkg_name = pname

				# build can contain two different prefixes
				# but with the same package name.
				prefix = dir_info["dir"] + ":" + pkg_name
				i_paths = map(lambda i: i["path"], go_file_json["imports"])
				if prefix not in jsons:
					jsons[prefix] = [go_file_json]
					package_imports[prefix] = i_paths
				else:
					jsons[prefix].append(go_file_json)
					package_imports[prefix] = package_imports[prefix] + i_paths

			#print dir_info["dir"]
			#print dir_info['files']
			#print "#%s#" % pkg_name
			if prefix in jsons:
				go_packages[prefix] = self.mergeGoSymbols(jsons[prefix])
				ip_packages[prefix] = dir_info["dir"]
				package_imports[prefix] = list(set(package_imports[prefix]))

		self.symbols = go_packages
		self.symbols_position = ip_packages
		self.package_imports = package_imports
		self.imported_packages = ip_used
		self.test_directories = list(set(test_directories))

		return True

