from subprocess import PIPE
from subprocess import Popen
import os
import sys

RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'
CYAN = '\033[96m'
WHITE = '\033[97m'
YELLOW = '\033[93m'
MAGENTA = '\033[95m'
GREY = '\033[90m'
BLACK = '\033[90m'
DEFAULT = '\033[99m'
ENDC = '\033[0m'

def getScriptDir():
	return os.path.dirname(os.path.realpath(__file__))

LOG_LEVEL_ERROR = 0
LOG_LEVEL_WARNING = 1
LOG_LEVEL_INFO = 2

LOG_FILE = "/var/lib/gofed/gofed.log"

class Logger:

	def __init__(self, level=LOG_LEVEL_INFO):
		self.level = level
		#self.log_file = open(LOG_FILE, "w")
		self.log_file = sys.stderr

	#def __del__(self):
	#	self.log_file.close()	

	def log(self, msg, level=""):
		print msg
		print LOG_FILE

		if level == "":
			self.log_file.write("%s: %s\n" % (self.level, msg))
		else:
			self.log_file.write("%s: %s\n" % (level, msg))
		
class FormatedPrint:

	def __init__(self, formated=True):
		self.formated = formated

	def printError(self, msg):
		if self.formated:
			print "%sError: %s%s" % (RED, msg, ENDC)
		else:
			print "Error: %s" % msg

	def printWarning(self, msg):
		if self.formated:
			print "%sWarning: %s%s" % (YELLOW, msg, ENDC)
		else:
			print "Warning: %s" % msg

	def printInfo(self, msg):
		if self.formated:
			print "%s%s%s" % (BLUE, msg, ENDC)
		else:
			print "%s" % msg

	def printProgress(self, msg):
		if self.formated:
			print "%s%s%s" % (YELLOW, msg, ENDC)
		else:
			print "%s" % msg


def runCommand(cmd):
	#cmd = cmd.split(' ')
	process = Popen(cmd, stderr=PIPE, stdout=PIPE, shell=True)
	stdout, stderr = process.communicate()
	rt = process.returncode

	return stdout, stderr, rt


def inverseMap(mfnc):
	"""inverse mapping of multifunction

	Keyword arguments:
	mfnc -- multifunction
	"""
	imap = {}
	for key in mfnc:
		for image in mfnc[key]:
			if image not in imap:
				imap[image] = [key]
			else:
				imap[image].append(key)
	return imap

