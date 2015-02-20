#!/bin/python

import optparse
from modules.Packages import buildRequirementGraph, getSCC

def printSCC(scc):
	print "Cyclic dep detected (%s): %s" % (len(scc), ", ".join(scc))
		
if __name__ == "__main__":

	parser = optparse.OptionParser("%prog [-v]")

	parser.add_option(
	    "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
	    help = "Display all warnings and errors as well"
	)

	options, args = parser.parse_args()

	graph = buildRequirementGraph(options.verbose)
	scc = getSCC(graph)

	for comp in scc:
		if len(comp) > 1:
			printSCC(comp)

