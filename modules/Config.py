#!/bin/python

from Utils import getScriptDir

class Config:

	def __init__(self):
		cfg_file = getScriptDir() + "/../config/go2fed.conf"
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
		return self.getValueFromDb('branches')

	def getImportPathDb(self):
		return self.getValueFromDb('import_path_db')
		


if __name__ == "__main__":
	cfg = Config()
	print cfg.getBranches()
	print cfg.getImportPathDb()
