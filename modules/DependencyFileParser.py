from Base import Base
import json

class DependencyFileParser(Base):

	def __init__(self, deps_file):
		self.deps_file = deps_file

	def parseGLOCKFILE(self):
		lines = []
		try:
			with open(self.deps_file, 'r') as file:
				lines = file.read().split("\n")
		except IOError, e:
			sys.stderr.write("%s\n" % e)
			return FORMAT_UNKNOWN

		deps = {}
		# GLOCKFILE
		# package hash
		for line in lines:
			items = line.split(" ")
			if len(items) != 2:
				continue

			deps[items[0]] = items[1]

		return deps

	def parseGODEPSJSON(self):
		deps = {}
		try:
			with open(self.deps_file, 'r') as file:
				json_deps = json.loads(file.read())
		except IOError, e:
			sys.stderr.write("%s\n" % e)
			return {}

		if "Deps" not in json_deps:
			return {}

		for dep in json_deps["Deps"]:
			if "ImportPath" not in dep or "Rev" not in dep:
				continue

			ip = str(dep["ImportPath"])
			rev = str(dep["Rev"])
			deps[ip] = rev

		return deps

