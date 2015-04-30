from Utils import getScriptDir

class Config:

	def __init__(self):
		cfg_file = getScriptDir() + "/../config/gofed.conf"
		self.db = {}
		self.parseConfigFile(cfg_file)

	def parseConfigFile(self, cfg_file):
		lines = []
		with open(cfg_file, 'r') as file:
			lines = file.read().split('\n')

		for line in lines:
			line = line.strip()

			if line == '' or line[0] == '#':
				continue

			parts = line.split(':')
			key = parts[0]
			value = ':'.join(parts[1:])

			key = key.strip()
			value = value.strip()

			if key == '':
				continue

			self.db[key] = value

	def getValueFromDb(self, key):
		if key in self.db:
			return self.db[key]
		return ""

	def getBranches(self):
		branches = self.getValueFromDb('branches').split(" ")
		return filter(lambda b: b != "", branches) 

	def getUpdates(self):
		branches = self.getValueFromDb('updates').split(" ")
		return filter(lambda b: b != "", branches) 

	def getOverrides(self):
		branches = self.getValueFromDb('overrides').split(" ")
		return filter(lambda b: b != "", branches)

	def getImportPathDb(self):
		return self.getValueFromDb('import_path_db')
		
	def getRepoPathPrefix(self):
		return self.getValueFromDb('repo_path_prefix')

	def getFASUsername(self):
		return self.getValueFromDb('fasuser')

	def getSkippedDirectories(self):
		branches = self.getValueFromDb('skipped_directories').split(" ")
		return filter(lambda b: b != "", branches) 

	def getSkippedProvidesWithPrefix(self):
		branches = self.getValueFromDb('skipped_provides_with_prefix').split(" ")
		return filter(lambda b: b != "", branches) 

	def makePathAbsolute(self, path):
		if path == "":
			return ""
		if path[0] != "/":
			return "/var/lib/gofed/%s" % path
		else:
			return path


	def getGolangMapping(self):
		path = self.getValueFromDb('golang_mapping')
		return self.makePathAbsolute(path)

	def getGolangNativeImports(self):
		path = self.getValueFromDb('golang_native_imports')
		return self.makePathAbsolute(path)

	def getGolangPkgdb(self):
		path = self.getValueFromDb('golang_pkgdb')
		return self.makePathAbsolute(path)

	def getGolangPackages(self):
		path = self.getValueFromDb('golang_packages')
		return self.makePathAbsolute(path)

	def getGolangIp2pkgMapping(self):
		path = self.getValueFromDb('golang_ip2pkg_mapping')
		return self.makePathAbsolute(path)

	def getGolangRepos(self):
		path = self.getValueFromDb('golang_repos')
		return self.makePathAbsolute(path)

	def getGolangSecondaryIPs(self):
		path = self.getValueFromDb('golang_secondary_import_paths')
		return self.makePathAbsolute(path)


if __name__ == "__main__":
	cfg = Config()
	print cfg.getBranches()
	print cfg.getImportPathDb()
