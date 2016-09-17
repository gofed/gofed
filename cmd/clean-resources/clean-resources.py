import optparse
from infra.system.resources.resourceclientgc import ResourceClientGC
from infra.system.resources.resourceprovidergc import ResourceProviderGC

from cmdsignature.parser import CmdSignatureParser
from gofedlib.utils import getScriptDir
import os

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/%s.yml" % (cur_dir, os.path.basename(__file__).split(".")[0])

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	ResourceClientGC(options.verbose).oneRound()
	ResourceProviderGC(options.verbose).oneRound()
