import optparse
import sys
from modules.SpecParser import SpecParser
from modules.FilesDetector import FilesDetector
import logging
import os
import urllib2
from modules.Utils import GREEN, RED, ENDC, BLUE

from gofed_lib.importpathparserbuilder import ImportPathParserBuilder
from gofed_lib.urlbuilder.urlbuilder import UrlBuilder

def setOptions():

	parser = optparse.OptionParser("%prog [-a] [-c] [-d [-v]] [directory]")

	parser.add_option(
	    "", "-s", "--spec", dest="spec", action = "store_true", default = False,
	    help = "Fetch tarball for the current project and its commits in spec file"
	)

	return parser

def checkOptions(options):

	resource_set = False

	if options.spec:
		resource_set = True

	if not resource_set:
		logging.error("Resource target not specified")
		exit(1)

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
	sp = SpecParser(specfile)
	if not sp.parse():
		logging.error("Unable to parser %s: %s" % (specfile, sp.getError()))
		exit(1)

	# Get import path prefix and commit
	commit = sp.getMacro("commit")
	if commit == "":
		commit = sp.getMacro("rev")

	if commit == "":
		logging.error("commit/rev not found")
		exit(1)

	ipprefix = sp.getMacro("import_path")
	if ipprefix == "":
		logging.error("import path prefix not found")
		exit(1)

	print "%sipprefix: %s%s" % (GREEN, ipprefix, ENDC)
	print "%scommit: %s%s" % (GREEN, commit, ENDC)

	# Construct provider signature
	ipparser = ImportPathParserBuilder().buildWithLocalMapping()

	signature = ipparser.parse(ipprefix).getProviderSignature()

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

