import tempfile
import os
import sys
from modules.RemoteSpecParser import RemoteSpecParser
from modules.Utils import runCommand, inverseMap
from modules.Packages import loadPackages

script_dir = os.path.dirname(os.path.realpath(__file__))

def displayMapping(pkg, imap, fmt=False):
	if fmt:
		mlen = 0
		for arg in imap:
			mlen = max(mlen, len(arg))

		for arg in imap:
			print "%s%s -> %s" % (arg, " " * (mlen - len(arg)),  ",".join(imap[arg]))

	else:
		for arg in imap:
			print "%s:%s:%s" % (arg, pkg, ",".join(imap[arg]))

if __name__ == "__main__":

	packages = loadPackages()
	for pkg in packages:
		rsp_obj = RemoteSpecParser('master', pkg)
		if not rsp_obj.parse():
			sys.stderr.write("%s: %s" % (pkg, rsp_obj.getError()))
			continue

		provides = rsp_obj.getProvides()
		imap = inverseMap(provides)
		displayMapping(pkg, imap)
		
