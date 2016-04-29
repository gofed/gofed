import optparse
import sys
from gofed.modules.SpecParser import SpecParser
from gofed.modules.FilesDetector import FilesDetector
import logging
import os
import urllib2
from gofed_lib.utils import GREEN, RED, ENDC, BLUE

from gofed_lib.go.importpath.parserbuilder import ImportPathParserBuilder
from gofed_lib.providers.providerbuilder import ProviderBuilder
from gofed_lib.urlbuilder.builder import UrlBuilder

def setOptions():

	parser = optparse.OptionParser("%prog [-a] [-c] [-d [-v]] [directory]")

	parser.add_option(
	    "", "-s", "--spec", dest="spec", action = "store_true", default = False,
	    help = "Fetch tarball for the current project and its commits in spec file"
	)

	parser.add_option(
	    "", "", "--repo-prefix", dest="repoprefix", default = "",
	    help = "Fetch tarballs for project with given prefix"
	)

	return parser

def checkOptions(options):

	resource_set = False

	if options.spec:
		resource_set = True

	if not resource_set:
		logging.error("Resource target not specified")
		exit(1)

def getMacros(specfile, repo_prefix = ""):
	sp = SpecParser(specfile)
	if not sp.parse():
		logging.error("Unable to parse %s: %s" % (specfile, sp.getError()))
		exit(1)

	if repo_prefix == "":
		commit_key = "commit"
		rev_key = "rev"
		ipprefix_key = "import_path"
	else:
		commit_key = "%s_commit" % repo_prefix
		rev_key = "%s_rev" % repo_prefix
		ipprefix_key = "%s_import_path" % repo_prefix

	# Get import path prefix and commit
	commit = sp.getMacro(commit_key)
	if commit == "":
		commit = sp.getMacro(rev_key)

	if commit == "":
		logging.error("commit/rev not found")
		exit(1)

	ipprefix = sp.getMacro(ipprefix_key)
	if ipprefix == "":
		logging.error("import path prefix not found")
		exit(1)

	return {
		"commit": commit,
		"ipprefix": ipprefix
	}

if __name__ == "__main__":

	parser = setOptions()
	options, args = parser.parse_args()

	checkOptions(options)

	# Get spec file

	print "%sDetecting spec file in the current directory...%s" % (BLUE, ENDC)
	specfile =  FilesDetector().detect().getSpecfile()
	print "%s'%s' detected%s" % (GREEN, specfile, ENDC)

	# Get provider and commit
	print "%sParsing spec file%s" % (BLUE, ENDC)

	# Get import path prefix and commit
	macros = getMacros(specfile, options.repoprefix)
	commit = macros["commit"]
	ipprefix = macros["ipprefix"]

	print "%sipprefix: %s%s" % (GREEN, ipprefix, ENDC)
	print "%scommit: %s%s" % (GREEN, commit, ENDC)

	# Construct provider signature
	ipparser = ImportPathParserBuilder().buildWithLocalMapping()
	provider = ProviderBuilder().buildUpstreamWithLocalMapping()

	ipprefix = ipparser.parse(ipprefix).prefix()
	signature = provider.parse(ipprefix).signature()

	if signature["provider"] == "github":
		resource_url = UrlBuilder().buildGithubSourceCodeTarball(signature["username"], signature["project"], commit)
	else:
		raise ValueError("Unsupported provider: %s" % (signature["provider"]))

	# Download the tarball
	print "%sFetching %s ...%s" % (BLUE, resource_url, ENDC)
	target_file = "%s/%s" % (os.getcwd(), os.path.basename(resource_url))
	response = urllib2.urlopen(resource_url)
	with open(target_file, "w") as f:
		f.write(response.read())
		f.flush()

