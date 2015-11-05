from modules.DependencyApproximator import DependencyApproximator
from modules.Config import Config

import json
import datetime
import sys

from modules.ParserConfig import ParserConfig

import optparse

# get imported packages from GoSymbolsExtractor
# decompose packages into classes
# for each class read all commits from upstream repository
# for each list of commits find the closest possible commit to inserted commit (based on date)

# optionally get a list of imported packages for given subset of project's packages

def deps2GodepsJson(deps, import_path):
	json_content = {}
	json_content["ImportPath"] = import_path

	json_deps = []
	for ip in deps:
		json_dep = {}
		json_dep["ImportPath"] = deps[ip]["ImportPath"]
		json_dep["Comment"] = deps[ip]["Date"]
		json_dep["Rev"] = deps[ip]["Rev"]
		json_deps.append(json_dep)

	json_content["Deps"] = json_deps
	return json.dumps(json_content, indent=4, sort_keys=False)

if __name__ == "__main__":

	parser = optparse.OptionParser("%prog [-a] [-c] [-d [-v]] [directory]")

	parser.add_option_group( optparse.OptionGroup(parser, "directory", "Directory to inspect. If empty, current directory is used.") )

	parser.add_option(
	    "", "", "--json", dest="json", action = "store_true", default = False,
	    help = "Display dependencies as json (almost Godeps.json)"
	)

	parser.add_option(
            "", "", "--scan-all-dirs", dest="scanalldirs", action = "store_true", default = False,
            help = "Scan all dirs, including Godeps directory"
        )

	parser.add_option(
            "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
            help = "Verbose mode"
        )

	parser.add_option(
            "", "", "--skip-dirs", dest="skipdirs", default = "",
            help = "Scan all dirs except specified via SKIPDIRS. Directories are comma separated list."
        )

	parser.add_option(
            "", "", "--commit-date", dest="commitdate", default = "",
            help = "Set commit date for the project in %d/%m/%Y format"
        )

	parser.add_option(
            "", "", "--importpath", dest="importpath", default = "",
            help = "Set import path of the project"
        )

	options, args = parser.parse_args()

	path = "."
	if len(args):
		path = args[0]

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

	if options.commitdate == "":
		commit_date = int(datetime.datetime.strptime('29/09/2015', '%d/%m/%Y').strftime("%s"))
	else:
		commit_date = int(datetime.datetime.strptime(options.commidate, '%d/%m/%Y').strftime("%s"))

	if options.importpath == "":
		importpath = "github.com/influxdb/influxdb"
	else:
		importpath = options.importpath

	parser_config = ParserConfig()
	parser_config.setSkipErrors()
	parser_config.setNoGodeps(noGodeps)
	parser_config.setImportsOnly()
	parser_config.setParsePath(path)
	parser_config.setImportPathPrefix(importpath)

	if not options.json:
		sys.stderr.write("Missing --json option\n")
		exit(1)

	da_obj = DependencyApproximator(parser_config, commit_date, verbose=options.verbose)
	da_obj.construct()
	#print da_obj.getError()

	deps = da_obj.getDependencies()
	print deps2GodepsJson(deps, importpath)
