from Config import Config
from Base import Base

class NativeImports(Base):

	def __init__(self):
		self.imports = []

	def retrieve(self):
		golang_native_imports = Config().getGolangNativeImports()
		try:
			with open(golang_native_imports, 'r') as file:
		                content = file.read()
				self.imports = filter(lambda i: i != '', content.split('\n'))
				return True
		except IOError, e:
			self.err = "Unable to read from %s: %s" % (golang_native_imports, e)

		return False

	def getImports(self):
		return self.imports

