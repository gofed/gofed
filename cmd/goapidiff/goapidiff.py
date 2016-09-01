# Check difference of APIs of two commits

# Output is number of symbols added and removed.
# You can list of those symbols as well

# Projects that change exported symbols with each commit should not be used
# as a built or install time dependency until they stabilize.

import logging

import os
from gofed_lib.utils import YELLOW, RED, BLUE, ENDC

from gofed_infra.system.core.factory.actfactory import ActFactory
from infra.system.core.factory.fakeactfactory import FakeActFactory
from gofed_lib.projectsignature.parser import ProjectSignatureParser

from infra.system.artefacts.artefacts import ARTEFACT_GOLANG_PROJECTS_API_DIFF

from cmdsignature.parser import CmdSignatureParser
from gofed_lib.utils import getScriptDir

def checkOptions(options):

	if options.prefix != "" and options.prefix[-1] == '/':
		logging.error("--prefix can not end with '/'")
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
			if options.prefix == "":
				line = print_removed(package)
			else:
				line = print_removed("%s/%s" % (options.prefix, package))
			if line:
				removed.append(line)

	# print new packages
	if (options.new or options.all) and "newpackages" in data:
		for package in data["newpackages"]:
			if options.prefix == "":
				line = print_new(package)
			else:
				line = print_new("%s/%s" % (options.prefix, package))
			if line:
				new.append(line)

	# print updated packages
	if "updatedpackages" in data:
		for package in data["updatedpackages"]:
			if options.prefix == "":
				package_name = package["package"]
			else:
				package_name = "%s/%s" % (options.prefix, package["package"])
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

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/%s.yml" % (cur_dir, os.path.basename(__file__).split(".")[0])

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

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
		data["reference"] = {
			"type": "user_directory",
			"resource": reference_project_signature["provider"]["location"]
		}

	if compare_with_project_signature["provider_type"] == "upstream_repository":
		data["compared_with"] = {
			"type": "upstream_source_code",
			"repository": compare_with_project_signature["provider"],
			"commit": compare_with_project_signature["commit"]
		}
	else:
		data["compared_with"] = {
			"type": "user_directory",
			"resource": compare_with_project_signature["provider"]["location"]
		}

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
