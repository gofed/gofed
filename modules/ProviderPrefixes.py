from Base import Base
from Config import Config

class ProviderPrefixes(Base):

	def loadCommonProviderPrefixes(self):
		golang_mapping_path = Config().getGolangCommonProviderPrefixes()
		try:
			with open(golang_mapping_path, 'r') as file:
				prefixes = []
				content = file.read()
				for line in content.split('\n'):
					if line == "" or line[0] == '#':
						continue

					prefixes.append( line.strip() )

				return True, prefixes
		except IOError, e:
			self.err = "Unable to read from %s: %s" % (golang_mapping_path, e)

		return False, []

