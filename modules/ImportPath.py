import re
from Config import Config

UNKNOWN = 0
GITHUB = 1
GOOGLECODE = 2
GOOGLEGOLANGORG = 3
GOLANGORG = 4
GOPKG = 5
BITBUCKET = 6

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

	def getProviderPrefix(self):
		return self.provider_prefix

	def parse(self):
		"""
		Parse import path into provider, project, repository.
		Returns True or False.
		"""
		url = re.sub(r'http://', '', self.import_path)
		url = re.sub(r'https://', '', url)

		custom_ip = self.parseCustomImportPaths(url)
		if custom_ip != {}:
			url = custom_ip["provider_prefix"]

		repo = self.detectKnownRepo(url)

		if repo == GITHUB:
			info = self.parseGithubImportPath(url)
		elif repo == GOOGLECODE:
			info = self.parseGooglecodeImportPath(url)
		elif repo == BITBUCKET:
			info = self.parseBitbucketImportPath(url)
		elif repo == GOPKG:
			info = self.parseGopkgImportPath(url)
		elif repo == GOOGLEGOLANGORG:
			info = self.parseGooglegolangImportPath(url)
		elif repo == GOLANGORG:
			info = self.parseGolangorgImportPath(url)
		else:
			self.err = "Import path %s not supported" % url
			return False

		if info == {}:
			return False

		self.provider = info["provider"]
		self.project = info["project"]
		self.repository = info["repo"]
		self.provider_prefix = info["provider_prefix"]
		if custom_ip != {}:
			self.prefix = custom_ip["prefix"]
		else:
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
		if url.startswith('google.golang.org'):
			return GOOGLEGOLANGORG

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
		repo["provider_prefix"] = "github.com/%s/%s" % (parts[1], parts[2])

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
		repo["provider_prefix"] = "code.google.com/p/%s" % (parts[2])

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
		repo["provider_prefix"] = "bitbucket.org/%s/%s" % (parts[1], parts[2])

		return repo

	def parseGopkgImportPath(self, path):
		"""
		Definition: gopkg.in/<v>/<repo> || gopkg.in/<repo>.<v>
		"""		
		parts = path.split('/')
		if re.match('v[0-9]+', parts[1]):
			if len(parts) < 3:
				self.err = "Import path %s is not in gopkg.in/<v>/<repo> form" % path
				return {}

			repository = parts[2]
			prefix = "/".join(parts[:3])
			provider_prefix = "gopkg.in/%s/%s" % (parts[1], parts[2])
		else:
			if len(parts) < 2:
				self.err = "Import path %s is not in gopkg.in/<repo>.<v> form" % path
				return {}

			prefix = "/".join(parts[:2])
			parts = parts[1].split(".")
			if len(parts) != 2:
				self.err = "Import path %s is not in gopkg.in/<repo>.<v> form" % path
				return {}

			repository = parts[0]
			provider_prefix = "gopkg.in/%s.%s" % (parts[0], parts[1])

		repo = {}
		repo["provider"] = GOPKG
		repo["project"] = ""
		repo["repo"] = repository
		repo["prefix"] = prefix
		repo["provider_prefix"] = provider_prefix

		return repo

	def parseGooglegolangImportPath(self, path):
		"""
		Definition:  google.golang.org/<repo>
		"""
		parts = path.split("/")

		if len(parts) < 2:
			self.err = "Import path %s is not in google.golang.org/<repo> form" % path
			return {}

		repo = {}
		repo["provider"] = GOOGLEGOLANGORG
		repo["project"] = ""
		repo["repo"] = parts[1]
		repo["prefix"] = "/".join(parts[:2])
		repo["provider_prefix"] = "google.golang.org/%s" % (parts[1])

		return repo

	def parseGolangorgImportPath(self, path):
		"""
		Definition:  golang.org/x/<repo>
		"""
		parts = path.split("/")

		if len(parts) < 3:
			self.err = "Import path %s is not in golang.org/x/<repo> form" % path
			return {}

		repo = {}
		repo["provider"] = GOLANGORG
		repo["project"] = ""
		repo["repo"] = parts[2]
		repo["prefix"] = "/".join(parts[:3])
		repo["provider_prefix"] = "golang.org/x/%s" % (parts[2])

		return repo

	def parseCustomImportPaths(self, path):
		"""
		Some import paths does not reflect provider prefix
		e.g. camlistore.org/pkg/googlestorage is actually at
		github.com/camlistore/camlistore repository under
		pkg/googlestorage directory. Read the list of customized
		import paths from golang.customized_imports
		"""
		ok, customized_prefix = self.getCustomizedImportsMappings()
		if not ok:
			return {}

		for prefix in customized_prefix:
			if path.startswith(prefix):
				return {"prefix": prefix, "provider_prefix": customized_prefix[prefix]}

		return {}

	def getPackageName(self):
		"""
		Package name construction is based on provider, not on prefix.
		Prefix does not have to equal provider_prefix.
		"""
		ok, mappings = self.getMappings()
		if not ok:
			return ""

		if self.provider_prefix in mappings:
			return mappings[self.provider_prefix]

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
		if self.provider == GOPKG:
			return self.gopkg2pkgdb(self.repository)

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
		return "golang-google-golangorg-%s" % repository

	def golangorg2pkgdb(self, repository):
		# golang.org/x/<repo>
		return "golang-golangorg-%s" % repository

	def gopkg2pkgdb(self, repository):
		# only gopkg.in/<v>/<repo>
		# or   gopkg.in/<repo>.<v>
		return "golang-gopkg-%s" % repository

	def getCustomizedImportsMappings(self):
		golang_mapping_path = Config().getGolangCustomizedImportsMapping()
		try:
			with open(golang_mapping_path, 'r') as file:
				maps = {}
				content = file.read()
				for line in content.split('\n'):
					if line == "" or line[0] == '#':
						continue
					line = re.sub(r'[\t ]+', ' ', line).split(' ')
					if len(line) != 2:
						continue
					maps[line[0]] = line[1]

				return True, maps
		except IOError, e:
			self.err = "Unable to read from %s: %s" % (golang_mapping_path, e)

		return False, {}

	def getMappings(self):
		golang_mapping_path = Config().getGolangMapping()
		try:
			with open(golang_mapping_path, 'r') as file:
				maps = {}
	        	        content = file.read()
				for line in content.split('\n'):
					if line == "" or line[0] == '#':
						continue
					line = re.sub(r'[\t ]+', ' ', line).split(' ')
					if len(line) != 2:
						continue
					maps[line[0]] = line[1]

				return True, maps
		except IOError, e:
			self.err = "Unable to read from %s: %s" % (golang_mapping_path, e)

		return False, {}
