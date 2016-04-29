from gofed_lib.logger.logger import Logger

import optparse
from modules.Utils import runCommand
import tempfile
import shutil
from time import time, strftime, gmtime
import sys
from modules.Utils import FormatedPrint
from modules.Config import Config

from gofed_infra.system.models.graphs.datasets.projectdatasetbuilder import ProjectDatasetBuilder
from gofed_infra.system.models.graphs.datasetdependencygraphbuilder import DatasetDependencyGraphBuilder
from gofed_infra.system.models.graphs.basicdependencyanalysis import BasicDependencyAnalysis
from gofed_lib.graphs.graphutils import GraphUtils
from gofed_infra.system.models.graphs.datasets.distributionlatestbuilds import DistributionLatestBuildGraphDataset
from gofed_lib.distribution.packagemanager import PackageManager
from gofed_infra.system.models.graphs.datasets.localprojectdatasetbuilder import LocalProjectDatasetBuilder
from gofed_lib.distribution.distributionnameparser import DistributionNameParser

def printSCC(scc):
	print "Cyclic dep detected (%s): %s" % (len(scc), ", ".join(scc))

def getGraphvizDotFormat(graph, results = {}):
	nodes = graph.nodes()
	edges = graph.edges()

	#digraph { a -> b; b -> c; c -> d; d -> a; }
	content = "digraph {\n"
	for u in nodes:
		if u in edges:
			for v in edges[u]:
				content += "\"%s\" -> \"%s\";\n" % (u.replace('-', '_'), v.replace('-', '_'))

	# add nodes with no outcoming edge
	if "leaves" in results:
		for leaf in results["leaves"]:
			content += "\"%s\" [style=filled, fillcolor=orange]" % leaf.replace('-', '_')

	# add nodes with no incomming edge
	if "roots" in results:
		for root in results["roots"]:
			content += "\"%s\" [style=filled, fillcolor=red3]" % root.replace('-', '_')

	# add cyclic deps
	if "cycles" in results:
		colors = ['purple', 'salmon', 'forestgreen', 'dodgerblue', 'yellow']
		col_len = len(colors)

		counter = 0
		for comp in results["cycles"]:
			for elem in comp:
				content += "\"%s\" [style=filled, fillcolor=%s]" % (elem.replace('-', '_'), colors[counter])
			counter = (counter + 1) % col_len

	content += "}\n"
	return content

def showGraph(graph, results, out_img = "./graph.png"):
	tmp_dir = tempfile.mkdtemp()
	try:
		f = open("%s/graph.dot" % (tmp_dir), "w")
	except IOError, e:
		sys.stderr.write("%s\n" % e)
		return

	f.write(getGraphvizDotFormat(graph, results))
	f.close()
	# fdp -Tpng test.dot > test.png
	so, se, rc = runCommand("fdp -Tpng %s/graph.dot > %s" % (tmp_dir, out_img))
	if rc != 0 or se != "":
		if se != "":
			print se
			return
		print "Unable to generate graph"
		return

	print "Graph saved to: %s\nYou can use eog %s to open it." % (out_img, out_img)
	# eog test.png
	shutil.rmtree(tmp_dir)

def setOptions():

	parser = optparse.OptionParser("%prog [-d --from-dir|--from-xml] -c|-l|-r|-g [-v] [PACKAGE]")

	parser.add_option(
	    "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
	    help = "Verbose mode"
	)

	parser.add_option(
	    "", "", "--target", dest="target", default = "Fedora:rawhide",
	    help = "Target distribution in a form OS:version, e.g. Fedora:f24. Implicitly set to Fedora:rawhide"
	)

	parser.add_option(
	    "", "-c", "--cyclic", dest="cyclic", action = "store_true", default = False,
	    help = "Get cyclic dependencies between golang packages"
	)

	parser.add_option(
	    "", "-l", "--leaves", dest="leaves", action = "store_true", default = False,
	    help = "Get golang packages without dependencies, only native imports"
	)

	parser.add_option(
	    "", "-r", "--roots", dest="roots", action = "store_true", default = False,
	    help = "Get golang packages not required by any package"
	)

	parser.add_option(
	    "", "-g", "--graphviz", dest="graphviz", action = "store_true", default = False,
	    help = "Output graph in a graphviz dot format. Red are packages not required, orange leaf packages, colored are packages with cyclic dependency."
	)

	parser.add_option(
	    "", "-o", "--outfile", dest="outfile", default = "",
	    help = "Name of files to save graph to. Default is graph.png"
	)

	parser.add_option(
	    "", "-d", "--decompose", dest="decompose", default = "",
	    help = "Import path of a project to decompose"
	)

	parser.add_option(
	    "", "", "--from-xml", dest="fromxml", default = "",
	    help = "Read project from xml file"
	)

	parser.add_option(
	    "", "", "--from-dir", dest="fromdir", default = "",
	    help = "Read project from directory"
	)

	parser.add_option(
            "", "", "--skip-errors", dest="skiperrors", action = "store_true", default = False,
            help = "Skip all errors during Go symbol parsing"
        )

	parser.add_option(
            "", "", "--scan-all-dirs", dest="scanalldirs", action = "store_true", default = False,
            help = "Scan all dirs, including Godeps directory"
        )

	parser.add_option(
            "", "", "--skip-dirs", dest="skipdirs", default = "",
            help = "Scan all dirs except specified via SKIPDIRS. Directories are comma separated list."
        )

	parser.add_option_group( optparse.OptionGroup(parser, "PACKAGE", "Display the smallest subgraph containing PACKAGE and all its dependencies.") )

	parser.add_option(
            "", "", "--package-level", dest="packagelevel", action = "store_true", default = False,
            help = "Analyze graph on a level of golang packages. Default is on an rpm level"
        )

	parser.add_option(
            "", "", "--no-list", dest="nolist", action = "store_true", default = False,
            help = "When listing cycles, leaves or roots, show just number of occurrences"
        )

	parser.add_option(
	    "", "", "--dry-run", dest="dryrun", action = "store_true", default = False,
	    help = "Run dry scan"
	)

	return parser

if __name__ == "__main__":
	# TODO(jchaloup): add option to show missing packages/deps

	# get list of tools/packages providing go binary
	options, args = setOptions().parse_args()
	pkg_name = ""
	if len(args) > 0:
		pkg_name = args[0]

	Logger.set(options.verbose)

	fp = FormatedPrint()

	scan_time_start = time()
	if not options.cyclic and not options.leaves and not options.roots and not options.graphviz:
		print "Synopsis: prog [-d --from-dir|--from-xml] -c|-l|-r|-g [-v] [PACKAGE]"
		exit(1)

	scan_time_start = time()
	if options.decompose != "":
		if options.fromdir == "":
			fp.printError("--from-dir option is missing")
			exit(1)
		dataset = LocalProjectDatasetBuilder(options.fromdir, options.decompose).build()
		graph = DatasetDependencyGraphBuilder().build(dataset, 2)
	else:
		try:
			distribution = DistributionNameParser().parse(options.target).signature()
		except ValueError as e:
			logging.error(e)
			exit(1)

		print "Extracting data from source code"
		# TODO(jchaloup): saving dataset?
		dataset = DistributionLatestBuildGraphDataset(options.dryrun).build(distribution)
		if options.packagelevel:
			graph = DatasetDependencyGraphBuilder().build(dataset, 2)
		else:
			graph = DatasetDependencyGraphBuilder().build(dataset, 1)


	scan_time_end = time()
	print strftime("Completed in %Hh %Mm %Ss", gmtime(scan_time_end - scan_time_start))

	# draw the graph
	if options.cyclic or options.leaves or options.roots or options.graphviz:
		nodes = graph.nodes()
		graph_cnt = len(nodes)

		if pkg_name != "":
			graph = GraphUtils.truncateGraph(graph, [pkg_name])
			subgraph_cnt = len(graph.nodes())
			
		if pkg_name != "":
			print "%s nodes of %s" % (subgraph_cnt, graph_cnt)
		else:
			print "%s nodes in total" % (graph_cnt)

		results = BasicDependencyAnalysis(graph).analyse().results()

		if not options.graphviz:
			if options.cyclic:
				if not options.nolist:
					for comp in results["cycles"]:
						printSCC(comp)
				print "\nNumber of cycles: %s" % len(results["cycles"])

			if options.leaves:
				if not options.nolist:
					for leaf in results["leaves"]:
						print leaf
				print "\nNumber of leaves: %s" % len(results["leaves"])

			if options.roots:
				if not options.nolist:
					for root in results["roots"]:
						print root
				print "\nNumber of roots: %s" % len(results["roots"])

		else:
			if options.outfile != "":
				showGraph(graph, results, options.outfile)
			else:
				showGraph(graph, results)
