class Base(object):

	def __init__(self):
		self.err = ""
		self.warn = ""

	def getError(self):
		return self.err

	def getWarning(self):
		return self.warn

