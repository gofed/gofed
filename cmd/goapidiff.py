# Check difference of APIs of two commits

# Output is number of symbols added and removed.
# You can list of those symbols as well

# Projects that change exported symbols with each commit should not be used
# as a built or install time dependency until they stabilize.

import logging

import optparse
from gofed_lib.utils import YELLOW, RED, BLUE, ENDC

from gofed_infra.system.core.factory.actfactory import ActFactory
from infra.system.core.factory.fakeactfactory import FakeActFactory
from gofed_lib.projectsignature.parser import ProjectSignatureParser

from infra.system.artefacts.artefacts import ARTEFACT_GOLANG_PROJECTS_API_DIFF

def setOptions():

	parser = optparse.OptionParser("prog [-e] [-d] DIR1 DIR2")

	parser.add_option(
	    "", "-c", "--color", dest="color", action = "store_true", default = False,
	    help = "Color output."
	)

	parser.add_option(
	    "", "-v", "--verbose", dest="verbose", action = "store_true", default = False,
	    help = "Verbose mode."
	)

	parser.add_option(
	    "", "-a", "--all", dest="all", action = "store_true", default = False,
	    help = "Show all differences between APIs"
	)

	parser.add_option(
	    "", "-n", "--new", dest="new", action = "store_true", default = False,
	    help = "Show new symbols in API"
	)

	parser.add_option(
	    "", "-r", "--removed", dest="removed", action = "store_true", default = False,
	    help = "Show removed symbols in API"
	)

	parser.add_option(
	    "", "-u", "--updated", dest="updated", action = "store_true", default = False,
	    help = "Show updated symbols in API"
	)

	parser.add_option(
	    "", "-s", "--sorted", dest="sorted", action = "store_true", default = False,
	    help = "Sort all changes by state and name"
	)

	parser.add_option(
	    "", "", "--prefix", dest="prefix", default = "",
	    help = "Import paths prefix"
	)

	# project signature
	# - upstream repository:commit
	# - user directory:ipprefix
	# - distribution package:build
	# For all I need their signature. How is the signature going to be specified?
	#
	# When specifying upstream repository, user must already know project (he knows prefix)
	# -> mapping
	#
	# upstream repo with ipprefix (automatically convert to provider prefix)
	# user directory (nothing to convert)
	# distribution with ipprefix (automatically convert to package)
	#
	# Examples:
	# - upstream:github.com/coreos/etcd[:commit]	take the latest if commit not specified
	# - user[:ipprefix]
	# - distro:Fedora[:f23][:package]		take rawhide if version not specified
	#						detect the package if not specified
	#
	# When specifying upstream both ipprefix and provider_prefix are equivalent.
	# The prefix is always converted to provider_prefix (c(provider_prefix) = provider_prefix)
	# Optionaly, the signature can be load from a file, options overrides file's signature properties
	parser.add_option(
	    "", "", "--reference", dest="reference", default = "",
	    help = "Reference project, e.g. upstream:github.com/username/project[:commit]"
	)

	parser.add_option(
	    "", "", "--compare-with", dest="comparewith", default = "",
	    help = "Project to compare with, e.g. user:gopkg.in/v1/yaml"
	)

	parser.add_option(
	    "", "", "--dry-run", dest="dryrun", action = "store_true", default = False,
	    help = "Run dry scan"
	)

	return parser

def checkOptions(options):

	if options.prefix != "" and options.prefix[-1] == '/':
		logging.error("--prefix can not end with '/'")
		exit(1)

	if options.reference == "":
		logging.error("--reference must be non-zero length string")
		exit(1)

	if options.comparewith == "":
		logging.error("--compare-with must be non-zero length string")
		exit(1)

def displayApiDifference(data, options):

	color = options.color
	prefix = options.prefix

	data = data["data"]

	def print_removed(item):
		if color:
			return "%s-%s%s" % (RED, item, ENDC)
		else:
			return "-%s" % item

	def print_new(item):
		if color:
			return "%s+%s%s" % (BLUE, item, ENDC)
		else:
			return "+%s" % item

	def print_updated(item):
		if color:
			return "%s~%s%s" % (YELLOW, item, ENDC)
		else:
			return "~%s" % item

	# if no option set, print removed symbols
	if not options.all and not options.removed and not options.new and not options.updated:
		options.removed = True

	new = []
	removed = []
	updated = []

	# print removed packages
	if (options.removed or options.all) and "removedpackages" in data:
		for package in data["removedpackages"]:
			line = print_removed(package)
			if line:
				removed.append(line)

	# print new packages
	if (options.new or options.all) and "newpackages" in data:
		for package in data["newpackages"]:
			line = print_new(package)
			if line:
				new.append(line)

	# print updated packages
	if "updatedpackages" in data:
		for package in data["updatedpackages"]:
			package_name = package["package"]
			for symbol_type in package:
				if symbol_type == "package":
					continue
				if symbol_type == "functions":
					prefix = "function"
				elif symbol_type == "types":
					prefix = "type"
				elif symbol_type == "variables":
					prefix = "variable"
				else:
					raise ValueError("Unsupported symbol type: %s" % symbol_type)
	
				for state in package[symbol_type]:
					for symbol in package[symbol_type][state]:
						if state.startswith("new"):
							line = print_new("%s: new %s: %s" % (package_name, prefix, symbol))
							if line and (options.new or options.all):
								new.append(line)
								if not options.sorted:
									print line
	
						if state.startswith("removed"):
							line = print_removed("%s: %s removed: %s" % (package_name, prefix, symbol))
							if line and (options.removed or options.all):
								removed.append(line)
								if not options.sorted:
									print line
	
	
						if state.startswith("updated"):
							line = print_updated("%s: %s updated: %s" % (package_name, prefix, symbol))
	
							if line and (options.updated or options.all):
								updated.append(line)
								if not options.sorted:
									print line

	if options.sorted:
		for line in sorted(new):
			print line

		for line in sorted(removed):
			print line

		for line in sorted(updated):
			print line

if __name__ == "__main__":

	options, args = setOptions().parse_args()

	checkOptions(options)

	try:
		reference_project_signature = ProjectSignatureParser().parse(options.reference)
	except ValueError as e:
		logging.error(e)
		exit(1)

	try:
		compare_with_project_signature = ProjectSignatureParser().parse(options.comparewith)
	except ValueError as e:
		logging.error(e)
		exit(1)

	data = {"reference": {}, "compared_with": {}}

	if reference_project_signature["provider_type"] == "upstream_repository":
		data["reference"] = {
			"type": "upstream_source_code",
			"repository": reference_project_signature["provider"],
			"commit": reference_project_signature["commit"]
		}
	else:
		data["reference"] = "user_directory",
		data["resource"] = reference_project_signature["provider"]["location"]

	if compare_with_project_signature["provider_type"] == "upstream_repository":
		data["compared_with"] = {
			"type": "upstream_source_code",
			"repository": compare_with_project_signature["provider"],
			"commit": compare_with_project_signature["commit"]
		}
	else:
		data["compared_with"] = "user_directory",
		data["compared_with"] = compare_with_project_signature["provider"]["location"]

	if options.dryrun:
		act_factory = FakeActFactory()
	else:
		act_factory = ActFactory()

	try:
		data = act_factory.bake("go-exported-api-diff").call(data)
	except Exception as e:
		logging.error(e)
		exit(1)

	displayApiDifference(data[ARTEFACT_GOLANG_PROJECTS_API_DIFF], options)
