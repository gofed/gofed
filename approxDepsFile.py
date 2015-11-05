from modules.DependencyApproximator import DependencyApproximator
from modules.Config import Config

import json
import datetime

from modules.ParserConfig import ParserConfig

# get imported packages from GoSymbolsExtractor
# decompose packages into classes
# for each class read all commits from upstream repository
# for each list of commits find the closest possible commit to inserted commit (based on date)

# optionally get a list of imported packages for given subset of project's packages

def detectProjectSubpackages(prefix, imported_packages):
	subpackages = []
	prefix_len = len(prefix)
	for ip in imported_packages:
		if ip.startswith(prefix):
			subpackage = ip[prefix_len:]
			if subpackage == "":
				subpackage = "."
			else:
				subpackage = subpackage[1:]
			subpackages.append( subpackage )

	return subpackages


if __name__ == "__main__":

	path = "."
	commit_date = int(datetime.datetime.strptime('29/09/2015', '%d/%m/%Y').strftime("%s"))
	noGodeps = Config().getSkippedDirectories()
	importpath = "github.com/influxdb/influxdb"

	parser_config = ParserConfig()
	parser_config.setSkipErrors()
	parser_config.setNoGodeps(noGodeps)
	parser_config.setImportsOnly()
	parser_config.setParsePath(path)
	parser_config.setImportPathPrefix(importpath)

	da_obj = DependencyApproximator(parser_config)
	da_obj.construct()
	print da_obj.getError()



	#json_file["Deps"] = json_deps

	#print json.dumps(json_file, indent=4, sort_keys=False)

