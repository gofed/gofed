# Check difference of APIs of two commits

# Output is number of symbols added and removed.
# You can list of those symbols as well

# Projects that change exported symbols with each commit should not be used
# as a built or install time dependency until they stabilize.

import logging

import os
from gofedlib.utils import YELLOW, RED, BLUE, ENDC

from gofedlib.projectsignature.parser import ProjectSignatureParser
from gofedlib.providers.providerbuilder import ProviderBuilder

from gofedinfra.system.artefacts.artefacts import ARTEFACT_GOLANG_PROJECTS_API_DIFF

from cmdsignature.parser import CmdSignatureParser
from gofedlib.utils import getScriptDir
from infra.system.workers import Worker
from infra.system.plugins.simplefilestorage.storagereader import StorageReader

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

	if options.verbose:
		logging.basicConfig(level=logging.WARNING)
	else:
		logging.basicConfig(level=logging.ERROR)

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

	repository_signature = {}
	hexsha1 = ""
	hesxha2 = ""
	local = False

	payload = {
		"ipprefix": options.prefix,
	}

	if reference_project_signature["provider_type"] == "upstream_repository":
		hexsha1 = reference_project_signature["commit"]
		payload["hexsha1"] = hexsha1
		payload["repository"] = reference_project_signature["provider"].prefix()
	else:
		hexsha1 = "local"
		local = True
		payload["directory1"] = reference_project_signature["provider"]["location"]

	if compare_with_project_signature["provider_type"] == "upstream_repository":
		repository_signature = compare_with_project_signature["provider"].signature()
		hexsha2 = compare_with_project_signature["commit"]
		payload["hexsha2"] = hexsha2
		payload["repository"] = compare_with_project_signature["provider"].prefix()
	else:
		hexsha2 = "local"
		local = True
		payload["directory2"] = compare_with_project_signature["provider"]["location"]

	if local:
		artefact_key = {
			"artefact": ARTEFACT_GOLANG_PROJECTS_API_DIFF,
			"repository": ProviderBuilder().buildUpstreamWithLocalMapping().parse("github.com/local/local").signature(),
			"commit1": hexsha1,
			"commit2": hexsha2,
		}
	else:
		artefact_key = {
			"artefact": ARTEFACT_GOLANG_PROJECTS_API_DIFF,
			"repository": repository_signature,
			"commit1": hexsha1,
			"commit2": hexsha2,
		}

	if local:
		Worker("goexportedapidiff").setPayload(payload).do()
	else:
		try:
			artefact = StorageReader().retrieve(artefact_key)
		except KeyError:
			Worker("goexportedapidiff").setPayload(payload).do()
	try:
		artefact = StorageReader().retrieve(artefact_key)
	except KeyError as err:
		logging.error(err)
		exit(1)

	displayApiDifference(artefact, options)
