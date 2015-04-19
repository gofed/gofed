import re
from Utils import getScriptDir

UNKNOWN = 0
GITHUB = 1
GOOGLECODE = 2
GOOGLEGOLANGORG = 3
GOLANGORG = 4
GOPKG = 5
BITBUCKET = 6

script_dir = getScriptDir() + "/.."
GOLANG_MAPPING="data/golang.mapping"

class ImportPath(object):
	"""
	Parses information from given
	import path:
		provider
		project
		repository
		prefix
	"""

	def __init__(self, import_path):
		self.import_path = import_path
		self.err = ""
		self.provider = UNKNOWN
		self.provider_prefix = ""
		self.project = ""
		self.repository = ""
		self.prefix = ""

	def getError(self):
		return self.err

	def getProvider(self):
		return self.provider

	def getProject(self):
		return self.project

	def getRepository(self):
		return self.repository

	def getPrefix(self):
		return self.prefix
	
	def parse(self):
		"""
		Parse import path into provider, project, repository.
		Returns True or False.
		"""
		url = re.sub(r'http://', '', self.import_path)
		url = re.sub(r'https://', '', url)

		repo = self.detectKnownRepo(url)

		if repo == GITHUB:
			info = self.parseGithubImportPath(url)
		elif repo == GOOGLECODE:
			info = self.parseGooglecodeImportPath(url)
		elif repo == BITBUCKET:
			info = self.parseBitbucketImportPath(url)
		else:
			self.err = "Import path %s not supported" % url
			return False

		if info == {}:
			return False

		self.provider = info["provider"]
		self.project = info["project"]
		self.repository = info["repo"]
		self.prefix = info["prefix"]

		return True

	def detectKnownRepo(self, url):
		"""
		For given import path detect provider.
		"""
		if url.startswith('github.com'):
			return GITHUB
		if url.startswith('code.google.com/p'):
			return GOOGLECODE
		if url.startswith('golang.org/x'):
			return GOLANGORG
		if url.startswith('gopkg.in'):
			return GOPKG
		if url.startswith('bitbucket.org'):
			return BITBUCKET

		return UNKNOWN

	def parseGithubImportPath(self, path):
		"""
		Definition: github.com/<project>/<repo>
		"""
		parts = path.split("/")

		if len(parts) < 3:
			self.err = "Import path %s not in github.com/<project>/<repo> form" % path
			return {}

		repo = {}
		repo["provider"] = GITHUB
		repo["project"] = parts[1]
		repo["repo"] = parts[2]
		repo["prefix"] = "/".join(parts[:3])

		return repo

	def parseGooglecodeImportPath(self, path):
		"""
		Definition: code.google.com/p/<repo>
		"""
		parts = path.split("/")

		if len(parts) < 3:
			self.err = "Import path %s is not in code.google.com/p/ form" % path
			return {}

		repo = {}
		repo["provider"] = GOOGLECODE
		repo["project"] = parts[1]
		repo["repo"] = parts[2]
		repo["prefix"] = "/".join(parts[:3])

		return repo

	def parseBitbucketImportPath(self, path):
		"""
		Definition: bitbucket.org/<project>/<repo>
		"""
		parts = path.split("/")

		if len(parts) < 3:
			self.err = "Import path %s is not in bitbucket.org/<project>/<repo> form" % path
			return {}

		repo = {}
		repo["provider"] = BITBUCKET
		repo["project"] = parts[1]
		repo["repo"] = parts[2]
		repo["prefix"] = "/".join(parts[:3])

		return repo

	def getPackageName(self):
		mappings = self.getMappings()

		if self.prefix in mappings:
			return mappings[self.prefix]

		if self.provider == GITHUB:
			return self.github2pkgdb(self.project, self.repository)
		if self.provider == BITBUCKET:
			return self.bitbucket2pkgdb(self.project, self.repository)
		if self.provider == GOOGLECODE:
			return self.googlecode2pkgdb(self.repository)
		if self.provider == GOOGLEGOLANGORG:
			return self.googlegolangorg2pkgdb(self.repository) 
		if self.provider == GOLANGORG:
			return self.golangorg2pkgdb(self.repository)

		self.err = "Provider not supported"
		return ""

	def github2pkgdb(self, project, repository):
		# github.com/<project>/<repository>
		return "golang-github-%s-%s" % (project, repository)

	def bitbucket2pkgdb(self, project, repository):
		# bitbucket.org/<project>/<repository>
		return "golang-bitbucket-%s-%s" % (project, repository)

	def googlecode2pkgdb(self, repository):
		# code.google.com/p/<repository>
		# rotate the repo name
		nparts = repository.split('.')
		if len(nparts) > 2:
			self.err = "%s repo contains more than one dot in its name, not implemented" % repository
			return ""
		if len(nparts) == 2:
			return "golang-googlecode-%s" % (nparts[1] + "-" + nparts[0])
		else:
			return "golang-googlecode-%s" % repository
	       
	def googlegolangorg2pkgdb(self, repository):
		# google.golang.org/<repository>
		return "golang-google-golang-%s" % repository

	def golangorg2pkgdb(self, repository):
		# golang.org/x/<repo>
		return "golang-golangorg-%s" % repository

	def getMappings(self):
		with open('%s/%s' % (script_dir, GOLANG_MAPPING), 'r') as file:
			maps = {}
	                content = file.read()
			for line in content.split('\n'):
				if line == "" or line[0] == '#':
					continue
				line = re.sub(r'[\t ]+', ' ', line).split(' ')
				if len(line) != 2:
					continue
				maps[line[0]] = line[1]

			return maps

