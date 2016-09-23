from ProviderPrefixes import ProviderPrefixes
import os
import sys

from gofedlib.go.importpath.parserbuilder import ImportPathParserBuilder
from gofedlib.providers.providerbuilder import ProviderBuilder
from gofedlib.projectsignature.signature import ProjectSignatureGenerator
from gofedlib.utils import renderTemplate, getScriptDir

class SpecGenerator:

	def __init__(self, with_build = False, with_extra = False):
		self.with_build = with_build
		self.with_extra = with_extra

		self.file = sys.stdout

	def generate(self, artefact, file = sys.stdout):
		self.file = file

		commit = artefact["metadata"]["commit"]

		# build provider and parser
		upstream_provider = ProviderBuilder().buildUpstreamWithLocalMapping()
		ipparser = ImportPathParserBuilder().buildWithLocalMapping()

		# get import path prefix
		import_path_prefix = ipparser.parse(artefact["metadata"]["import_path"]).prefix()

		# get provider's signature and prefix
		upstream_provider.parse(import_path_prefix)
		provider_signature = upstream_provider.signature()
		provider_prefix = upstream_provider.prefix()

		project_signature = ProjectSignatureGenerator().generate(provider_signature, commit)

		# generate first level license and docs only
		licenses = filter(lambda l: len(l["file"].split("/")) == 1, artefact["data"]["licenses"])
		docs = filter(lambda l: len(l.split("/")) == 1, artefact["data"]["docs"])

		main_deps = {}
		main_dirs = []
		covered = []
		for package in artefact["data"]["mains"]:
			deps = filter(lambda l: not l.startswith(import_path_prefix), package["dependencies"])
			main_deps[package["path"]] = deps
			covered = covered + deps
			main_dirs.append(os.path.dirname(package["path"]))

		main_dirs = sorted(list(set(main_dirs)))

		# generate dependency on packages from devel not currently covered
		devel_deps = []
		if artefact["data"]["packages"]:
			devel_deps = reduce(lambda a,b: a+b, map(lambda l: filter(lambda l: not l.startswith(import_path_prefix), l["dependencies"]), artefact["data"]["packages"]))
			devel_deps = list(set(devel_deps))

		# provides
		provides = []
		for path in sorted(map(lambda l: l["package"], artefact["data"]["packages"])):
			# skip all provided packages with /internal/ keyword
			if "internal" in path.split("/"):
				continue

			sufix = ""
			if path != ".":
				sufix = "/%s" % path

			provides.append(sufix)

		# test deps
		test_imported_packages = []
		for test in artefact["data"]["tests"]:
			test_imported_packages.extend(test["dependencies"])

		test_deps = sorted(list(set(test_imported_packages) - set(devel_deps)))
		test_deps = filter(lambda l: not l.startswith(import_path_prefix), test_deps)

		test_directories = []
                for dir in sorted(map(lambda l: l["test"], artefact["data"]["tests"])):

			sufix = ""
			if dir != ".":
				sufix = "/%s" % dir

			test_directories.append(sufix)

		prefix_dir = {
			"type": "default"
		}
		if provider_signature["provider"] in ["github", "bitbucket"]:
			if import_path_prefix != provider_prefix:
				ip_prefix, _ = os.path.split(import_path_prefix)
				pp_obj = ProviderPrefixes()
				ok, prefixes = pp_obj.loadCommonProviderPrefixes()
				if not ok or ip_prefix not in prefixes:
					prefix_dir["type"] = "custom"
					prefix_dir["prefix"] = ip_prefix
				else:
					prefix_dir["type"] = "empty"

		# set template vars
		template_vars = {
			"with_build": self.with_build,
			"import_path_prefix": import_path_prefix,
			"prefix_dir": prefix_dir,
			"provider_prefix": provider_prefix,
			"project_signature": project_signature.json(),
			"licenses": licenses,
			"docs": docs,
			# TODO(jchaloup): set rrepo and stripped_repo for googlecode provider
			"rrepo": "net.go",
			"stripped_repo": "net",
			"main": {
				"dirs": main_dirs,
				"deps": main_deps,
				"remaining_devel_deps": list(set(devel_deps) - set(covered))
			},
			"devel": {
				"deps": sorted(devel_deps),
				"provides": provides
			},
			"tests": {
				"directories": test_directories,
				"deps": test_deps
			},
			"dependency_directories": artefact["data"]["dependency_directories"]
		}

		spec_content = renderTemplate(getScriptDir(__file__), "spec.jinja", template_vars)
		self.file.write(spec_content)

	def setOutputFile(self, file):
		self.file = file

