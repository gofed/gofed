import optparse
import sys
from gofed.modules.SpecParser import SpecParser
from gofed.modules.FilesDetector import FilesDetector
import logging
import os
import urllib2
from gofedlib.utils import GREEN, RED, ENDC, BLUE

from gofedlib.go.importpath.parserbuilder import ImportPathParserBuilder
from gofedlib.providers.providerbuilder import ProviderBuilder
from gofedlib.urlbuilder.builder import UrlBuilder

from cmdsignature.parser import CmdSignatureParser
from gofedlib.utils import getScriptDir

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

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/%s.yml" % (cur_dir, os.path.basename(__file__).split(".")[0])

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

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

