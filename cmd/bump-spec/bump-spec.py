import optparse
from gofed.modules.SpecParser import SpecParser

from gofedlib.go.importpath.parserbuilder import ImportPathParserBuilder
from gofedlib.providers.providerbuilder import ProviderBuilder
from gofedlib.repository.repositoryclientbuilder import RepositoryClientBuilder
from gofedlib.urlbuilder.builder import UrlBuilder
import urllib2
from gofedlib.utils import GREEN, RED, ENDC, BLUE, runCommand
import os

from cmdsignature.parser import CmdSignatureParser
from gofedlib.utils import getScriptDir

def getSpec():
	so, se, rc = runCommand("ls *.spec")
	if rc != 0:
		return ""
	else:
		return so.strip().split(" ")[0]

def getMacros(spec, repoprefix):

	err = ""
	macros = {}
	obj = SpecParser(spec)
	if not obj.parse():
		err = obj.getError()
		return err, {}, -1

	if repoprefix == "":
		macros["project"] = obj.getMacro("project")
		macros["repo"] = obj.getMacro("repo")
		macros["provider"] = obj.getMacro("provider")
		macros["commit"] = obj.getMacro("commit")
		macros["ip"] = obj.getMacro("provider_prefix")
		if macros["ip"] == "":
			macros["ip"] = obj.getMacro("import_path")

	else:
		macros["project"] = obj.getMacro("%s_project" % repoprefix)
		macros["repo"] = obj.getMacro("%s_repo" % repoprefix)
		macros["provider"] = obj.getMacro("%s_provider" % repoprefix)
		macros["commit"] = obj.getMacro("%s_commit" % repoprefix)
		macros["ip"] = obj.getMacro("%s_provider_prefix" % repoprefix)
		if macros["ip"] == "":
			macros["ip"] = obj.getMacro("%s_import_path" % repoprefix)

	last_bug_id = obj.getBugIdFromLastChangelog()

	if macros["project"] == "":
		err = "Unable to detect project macro"
		return err, {}, -1

	if macros["repo"] == "":
		err = "Unable to detect repo macro"
		return err, {}, -1

	if macros["provider"] == "":
		err = "unable to detect provider macro"
		return err, {}, -1

	if macros["commit"] == "":
		err = "unable to detect commit macro"
		return err, {}, -1

	if macros["ip"] == "":
		err = "Unable to detect provider URL"
		return err, {}, -1

	return "", macros, last_bug_id

def updateSpec(spec, commit, repoprefix):
	if repoprefix == "":
		commit_macro = "commit"
	else:
		commit_macro = "%s_commit" % repoprefix
	cmd = "sed -i -e \"s/%%global %s\([[:space:]]\+\)[[:xdigit:]]\{40\}/%%global %s\\1%s/\" %s" % (commit_macro, commit_macro, commit, spec)

	so, se, rc = runCommand(cmd)
	if rc != 0:
		return False
	else:
		return True

def bumpSpec(spec, commit, last_bug_id):
	if last_bug_id != -1:
		cmd = "rpmdev-bumpspec --comment=\"$(echo \"Bump to upstream %s\n  related: #%s\")\" %s" % (commit, last_bug_id, spec)
	else:
		cmd = "rpmdev-bumpspec --comment=\"Bump to upstream %s\" %s" % (commit, spec)

	so, se, rc = runCommand(cmd)
	if rc != 0:
		return False
	else:
		return True

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/bump-spec.yml" % (cur_dir)

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	# must be on master branch
	if not options.skipmaster:
		so, se, rc = runCommand("git branch | grep '*' | sed 's/*//'")
		if rc != 0:
			print "Not in a git repository"
			exit(1)

		branch = so.split('\n')[0].strip()
		if branch != "master":
			print "Not on branch master"
			exit(1)

	# get spec file
	print "Searching for spec file"
	spec = getSpec()
	if spec == "":
		print "Unable to find spec file"
		exit(1)

	# get macros
	print "Reading macros from %s" % spec
	err, macros, last_bug_id = getMacros(spec, options.repoprefix)
	if err != "":
		print err
		exit(2)

	# Construct provider signature
	ipparser = ImportPathParserBuilder().buildWithLocalMapping()
	provider = ProviderBuilder().buildUpstreamWithLocalMapping()

	ipprefix = ipparser.parse(macros["ip"]).prefix()
	signature = provider.parse(ipprefix).signature()

	commit = options.commit
	if commit == "":
		# get latest commit
		print "Retrieving the latest commit from %s" % macros["ip"]
		client = RepositoryClientBuilder().buildWithRemoteClient(signature)
		commit = client.latestCommit()["hexsha"]

	if signature["provider"] == "github":
		resource_url = UrlBuilder().buildGithubSourceCodeTarball(signature["username"], signature["project"], commit)
	elif signature["provider"] == "bitbucket":
		resource_url = UrlBuilder().buildBitbucketSourceCodeTarball(signature["username"], signature["project"], commit)
	else:
		raise ValueError("Unsupported provider: %s" % (signature["provider"]))

	current_commit = macros["commit"]

	# don't bump if the commit is equal to the latest
	if commit == current_commit:
		print "The latest commit equals the current commit"
		exit(1)

	if not options.skipchecks:
		if signature["provider"] == "github":
			client = RepositoryClientBuilder().buildWithRemoteClient(signature)
			tags = client.tags()
			releases = client.releases()

			print "Tags: " + ", ".join(tags[:5])
			print "Releases: " + ", ".join(releases[:5])

	# Download the tarball
	print "%sFetching %s ...%s" % (BLUE, resource_url, ENDC)
	target_file = "%s/%s" % (os.getcwd(), os.path.basename(resource_url))
	response = urllib2.urlopen(resource_url)
	with open(target_file, "w") as f:
		f.write(response.read())
		f.flush()

	# update spec file
	print "Updating spec file"
	if not updateSpec(spec, commit, options.repoprefix):
		print "Unable to update spec file"
		exit(5)

	# bump spec file
	if not options.nobump:
		print "Bumping spec file"
		if not bumpSpec(spec, commit, last_bug_id):
			print "Unable to bump spec file"
			exit(6)

