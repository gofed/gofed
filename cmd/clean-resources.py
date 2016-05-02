import optparse
from infra.system.resources.resourceclientgc import ResourceClientGC
from infra.system.resources.resourceprovidergc import ResourceProviderGC

def setOptions():
	parser = optparse.OptionParser("%prog [-v]")

	parser.add_option(
            "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
            help = "Show all packages if -d option is on"
        )

	return parser.parse_args()

if __name__ == "__main__":

	options, args = setOptions()

	ResourceClientGC(options.verbose).oneRound()
	ResourceProviderGC(options.verbose).oneRound()
