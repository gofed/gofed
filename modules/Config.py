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

if __name__ == "__main__":
	cfg = Config()
	print cfg.getBranches()
	print cfg.getImportPathDb()
