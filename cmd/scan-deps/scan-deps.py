from gofedlib.logger.logger import Logger

from gofed.modules.Utils import runCommand
import tempfile
import shutil
from time import time, strftime, gmtime
import sys
from gofed.modules.Utils import FormatedPrint
import os

from gofedinfra.system.models.graphs.datasets.projectdatasetbuilder import ProjectDatasetBuilder
from gofedinfra.system.models.graphs.datasetdependencygraphbuilder import DatasetDependencyGraphBuilder
from gofedinfra.system.models.graphs.basicdependencyanalysis import BasicDependencyAnalysis
from gofedinfra.system.models.graphs.datasets.distributionlatestbuilds import DistributionLatestBuildGraphDataset
from gofedinfra.system.models.graphs.datasets.localprojectdatasetbuilder import LocalProjectDatasetBuilder
from gofedlib.distribution.distributionnameparser import DistributionNameParser
from gofedlib.graphs.graphutils import GraphUtils

from cmdsignature.parser import CmdSignatureParser
from gofedlib.utils import getScriptDir

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
			if leaf not in nodes:
				continue
			content += "\"%s\" [style=filled, fillcolor=orange]" % leaf.replace('-', '_')

	# add nodes with no incomming edge
	if "roots" in results:
		for root in results["roots"]:
			if root not in nodes:
				continue
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

if __name__ == "__main__":
	# TODO(jchaloup): add option to show missing packages/deps

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/%s.yml" % (cur_dir, os.path.basename(__file__).split(".")[0])

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	# get list of tools/packages providing go binary
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
		graph = DatasetDependencyGraphBuilder().build(dataset, 2, pkg_name)
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
			graph = DatasetDependencyGraphBuilder().build(dataset, 2, pkg_name)
		else:
			graph = DatasetDependencyGraphBuilder().build(dataset, 1, pkg_name)

	scan_time_end = time()
	print strftime("Completed in %Hh %Mm %Ss", gmtime(scan_time_end - scan_time_start))

	# draw the graph
	if options.cyclic or options.leaves or options.roots or options.graphviz:
		nodes = graph.nodes()
		graph_cnt = len(nodes)

		print "%s nodes in total" % (graph_cnt)

		results = BasicDependencyAnalysis(graph).analyse().results()
		if options.skipunittest:
			# TODO(jchaloup): use Rpm to detect unit-test rpm instead of testing for substr
			graph = GraphUtils.filterGraph(graph, lambda l: "unit-test" not in l)
		nodes = graph.nodes()

		if not options.graphviz:
			if options.cyclic:
				if not options.nolist:
					for comp in results["cycles"]:
						printSCC(comp)
				print "\nNumber of cycles: %s" % len(results["cycles"])

			if options.leaves:
				if not options.nolist:
					for leaf in results["leaves"]:
						if leaf not in nodes:
							continue
						print leaf
				print "\nNumber of leaves: %s" % len(results["leaves"])

			if options.roots:
				if not options.nolist:
					for root in results["roots"]:
						if root not in nodes:
							continue
						print root
				print "\nNumber of roots: %s" % len(results["roots"])

		else:
			if not options.dryrun:
				if options.outfile != "":
					showGraph(graph, results, options.outfile)
				else:
					showGraph(graph, results)
