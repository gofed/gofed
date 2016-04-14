from os import walk
from Base import Base

class FilesDetector(Base):

	def __init__(self):
		self.specfile = ""
		self.sources = ""
		self.archive = ""

	def getSpecfile(self):
		return self.specfile

	def getSources(self):
		return self.sources

	def getArchive(self):
		return self.archive

	def detect(self):
		files = []

		self.specfile = ""
		self.sources = ""
		self.archive = ""

		for dirName, subdirList, fileList in walk("."):
			if dirName != ".":
				continue
			for fname in fileList:
				files.append(fname)


		for fname in files:
			if self.specfile == "" and fname.endswith(".spec"):
				self.specfile = fname
				continue

			if self.sources == "" and fname == "sources":
				self.sources = fname
				continue

			if self.archive == "":
				if fname.endswith(".gz"):
					self.archive = fname
				if fname.endswith(".zip"):
					self.archive = fname
				if fname.endswith(".xz"):
					self.archive = name
				continue

			if self.specfile != "" and self.sources != "" and self.archive != "":
				break

		return self
