import optparse
from modules.Packages import getSCC, getLeafPackages, getRootPackages, ConnectedComponent, joinGraphs
from modules.Utils import runCommand
import tempfile
import shutil
from time import time, strftime, gmtime
import sys
from modules.DependencyGraphBuilder import DependencyGraphBuilder
from modules.ProjectDecompositionGraphBuilder import ProjectDecompositionGraphBuilder
from modules.Utils import FormatedPrint
from modules.Config import Config

def printSCC(scc):
	print "Cyclic dep detected (%s): %s" % (len(scc), ", ".join(scc))

def getGraphvizDotFormat(graph):
	nodes, edges = graph

	#digraph { a -> b; b -> c; c -> d; d -> a; }
	content = "digraph {\n"
	for u in nodes:
		if u in edges:
			for v in edges[u]:
				content += "\"%s\" -> \"%s\";\n" % (u.replace('-', '_'), v.replace('-', '_'))

	# add nodes with no outcoming edge
	leaves = getLeafPackages(graph)
	for leaf in leaves:
		content += "\"%s\" [style=filled, fillcolor=orange]" % leaf.replace('-', '_')

	# add nodes with no incomming edge
	roots = getRootPackages(graph)
	for root in roots:
		content += "\"%s\" [style=filled, fillcolor=red3]" % root.replace('-', '_')

	# add cyclic deps
	scc = getSCC(graph)

	colors = ['purple', 'salmon', 'forestgreen', 'dodgerblue', 'yellow']
	col_len = len(colors)

	counter = 0
	for comp in scc:
		if len(comp) > 1:
			for elem in comp:
				content += "\"%s\" [style=filled, fillcolor=%s]" % (elem.replace('-', '_'), colors[counter])
			counter = (counter + 1) % col_len


	content += "}\n"
	return content

def showGraph(graph, out_img = "./graph.png"):
	tmp_dir = tempfile.mkdtemp()
	try:
		f = open("%s/graph.dot" % (tmp_dir), "w")
	except IOError, e:
		sys.stderr.write("%s\n" % e)
		return

	f.write(getGraphvizDotFormat(graph))
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

def truncateGraph(graph, pkg_name, pkg_devel_main_pkg):
	"""
	Return graph containing only pkg_name and all its dependencies
	"""
	# 1. get all devel subpackages belonging to pkg_name
	root_nodes = []
	for devel in pkg_devel_main_pkg:
		if pkg_devel_main_pkg[devel] == pkg_name:
			root_nodes.append(devel)

	# 2. create a set of all nodes containg the subpackages and
	# all nodes reacheable from them
	subgraph = None
	for node in root_nodes:
		cc = ConnectedComponent(graph, node)
		if subgraph == None:
			subgraph = cc.getCC()
		else:
			subgraph = joinGraphs(subgraph, cc.getCC())

	return subgraph
	
if __name__ == "__main__":

	parser = optparse.OptionParser("%prog [-d --from-dir|--from-xml] -c|-l|-r|-g [-v] [PACKAGE]")

	parser.add_option(
	    "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
	    help = "Display all warnings and errors as well"
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

	# get list of tools/packages providing go binary

	options, args = parser.parse_args()
	pkg_name = ""
	if len(args) > 0:
		pkg_name = args[0]

	if not options.scanalldirs:
		noGodeps = Config().getSkippedDirectories()
	else:
		noGodeps = []

	if options.skipdirs:
		for dir in options.skipdirs.split(','):
			dir = dir.strip()
			if dir == "":
				continue
			noGodeps.append(dir)

	fp = FormatedPrint()

	scan_time_start = time()
	if not options.cyclic and not options.leaves and not options.roots and not options.graphviz:
		print "Synopsis: prog [-d --from-dir|--from-xml] -c|-l|-r|-g [-v] [PACKAGE]"
		exit(1)

	if options.decompose != "":
		gb = ProjectDecompositionGraphBuilder(options.decompose, skip_errors=options.skiperrors, noGodeps=noGodeps)
		if options.fromxml != "":
			if not gb.buildFromXml(options.fromxml):
				fp.printError(gb.getError())
				exit(1)
		elif options.fromdir != "":
			if not gb.buildFromDirectory(options.fromdir):
				fp.printError(gb.getError())
				exit(1)
		else:
			fp.printError("--from-xml or --from-dir option is missing")
			exit(1)
	else:
		print "Reading packages..."
		gb = DependencyGraphBuilder(cache = True)
		if not gb.build():
			fp.printError(gb.getError())
			exit(1)

	# draw the graph
	if options.cyclic or options.leaves or options.roots or options.graphviz:
		graph = gb.getGraph()
		pkg_devel_main_pkg = gb.getSubpackageMembership()
		if options.verbose:
			warn = gb.getWarning()
			if warn != []:
				print "\n".join(map(lambda l: "Warning: %s" % l, warn))

		nodes, _ = graph
		graph_cnt = len(nodes)

		if pkg_name != "":
			graph = truncateGraph(graph, pkg_name, pkg_devel_main_pkg)
			if graph == None:
				print "No graph generated, package probably does not exist"
				exit(0)

			nodes, _ = graph
			subgraph_cnt = len(nodes)
			
		scan_time_end = time()
		print strftime("Completed in %Hh %Mm %Ss", gmtime(scan_time_end - scan_time_start))
		if pkg_name != "":
			print "%s nodes of %s" % (subgraph_cnt, graph_cnt)
		else:
			print "%s nodes in total" % (graph_cnt)


		if options.cyclic:
			scc = getSCC(graph)

			for comp in scc:
				if len(comp) > 1:
					printSCC(comp)

		elif options.leaves:
			leaves = getLeafPackages(graph)
			for leaf in leaves:
				print leaf

		elif options.roots:
			roots = getRootPackages(graph)
			for root in roots:
				print root

		elif options.graphviz:
			if options.outfile != "":
				showGraph(graph, options.outfile)
			else:
				showGraph(graph)
