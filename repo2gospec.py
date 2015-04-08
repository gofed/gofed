import optparse
from modules.Utils import ENDC, YELLOW, RED, GREEN, BLUE
from modules.Utils import runCommand
from modules.Repos import github2pkgdb, googlecode2pkgdb, bitbucket2pkgdb
from modules.Packages import packageInPkgdb
from modules.ImportPaths import decomposeImports
from modules.Repos import repo2pkgName, getGithubLatestCommit, getBitbucketLatestCommit

from modules.specParser import SpecGenerator, PROVIDER_GITHUB, PROVIDER_GOOGLECODE, PROVIDER_BITBUCKET
import os
import sys
import errno



def setOptions():
	parser = optparse.OptionParser("%prog [-e] [-d] file [file [file ...]]")

	sln = not (os.path.basename(sys.argv[0]) == "repo2spec.py")
	github = os.path.basename(sys.argv[0]) == "github2gospec"
	googlecode = os.path.basename(sys.argv[0]) == "googlecode2gospec"
	bitbucket = os.path.basename(sys.argv[0]) == "bitbucket2gospec"

	SH = optparse.SUPPRESS_HELP

	parser.add_option(
	    "", "", "--github", dest="github", action="store_true", default = False,
	    help = SH if sln else "github.com repository"
	)

	parser.add_option(
	    "", "", "--googlecode", dest="googlecode", action="store_true", default = False,
	    help = SH if sln else "code.google.com repository"
	)

	parser.add_option(
	    "", "", "--bitbucket", dest="bitbucket", action="store_true", default = False,
	    help = SH if sln else "bitbucket.org repository"
	)

	if github:
		help_text = "Repository name, github.com/project/REPO"
	elif googlecode:
		help_text = "Repository name, code.google.com/p/REPO"
	elif bitbucket:
		help_text = "Repository name, bitbucket.org/project/REPO"
	else:
		help_text = "Repository name, e.g. github.com/project/REPO"
	

	parser.add_option(
	    "", "-r", "--repo", dest="repo", default = "",
	    help = help_text
	)

	if github:
		help_text = "Repository name, github.com/PROJECT/repository"
	elif bitbucket:
		help_text = "Repository name, bitbucket.org/PROJECT/repository"
	else:
		help_text = "Repository name, e.g. github.com/PROJECT/repository"

	parser.add_option(
	    "", "-p", "--project", dest="project", default = "",
	    help = SH if googlecode else help_text
	)

	if googlecode:
		parser.add_option(
		    "", "-c", "--rev", dest="revision", default = "",
		    help = "Revision"
		)
	else:
		parser.add_option(
		    "", "-c", "--commit", dest="commit", default = "",
		    help = "Commit. If not specified the latest is taken."
		)

	parser.add_option(
	    "", "-f", "--format", dest="format", action="store_true", default = False,
	    help = "Make messages more shiny"
	)

	parser.add_option(
	    "", "", "--force", dest="force", action="store_true", default = False,
	    help = "Generate spec file even if it is already in Fedora"
	)

	return parser.parse_args()

def checkOptions(options):
	fail = False

	if not options.github and not options.googlecode and not options.bitbucket:
		print "No provider specified"
		fail = True

	if options.github or options.googlecode or options.bitbucket:
		if options.repo == "":
			print "Repository missing"
			fail = True

	if options.github or options.bitbucket:
		if options.project == "":
			print "Project missing"
			fail = True

	if options.googlecode:
		if options.revision == "":
			print "Revision missing"
			fail = True


	return fail

def printBasicInfo(url, commit, name):
	print "%sRepo URL: %s%s" % (YELLOW, url, ENDC)
	print "%sCommit: %s%s" % (YELLOW, commit, ENDC)
	print "%sName: %s%s" % (YELLOW, name, ENDC)

# http://stackoverflow.com/questions/273192/in-python-check-if-a-directory-exists-and-create-it-if-necessary
def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def isPkgInPkgDB(name, force):
	if packageInPkgdb(name):
		print "%sPackage %s already exists%s" % (RED, name, ENDC)
		if not force:
			exit(1)

def createBasicDirectories(name):
	make_sure_path_exists("%s/fedora/%s" % (name, name))
	os.chdir("%s/fedora/%s" % (name, name))

def downloadTarball(archive_url):
	so, se, rc = runCommand("wget -nv %s --no-check-certificate" % archive_url)
	if rc != 0:		
		print "%sUnable to download tarball:\n%s%s" % (RED, se, ENDC)
		exit(1)


if __name__ == "__main__":

	options, args = setOptions()

	if checkOptions(options):
		exit(1)

	if not options.format:
		ENDC = ""
		YELLOW = ""
		RED = ""
		BLUE = ""

	# collect spec file information
	project = options.project
	repo = options.repo

	if options.github:
		provider = PROVIDER_GITHUB
		url = "github.com/%s/%s" % (project, repo)
		name = github2pkgdb(url)
		if options.commit == "":
			print "%sGetting the latest commit from %s%s" % (BLUE, url, ENDC)
			commit = getGithubLatestCommit(project, repo)
			if commit == "":
				print "%sUnable to get the latest commit%s" % (RED, ENDC)
				exit(1)
			print ""
		else:
			commit = options.commit
		shortcommit = commit[:7]
		archive = "%s-%s.tar.gz" % (repo, shortcommit)
		archive_dir = "%s-%s" % (repo, commit)
		archive_url = "https://github.com/%s/%s/archive/%s/%s" % (project, repo, commit, archive)
	elif options.googlecode:
		provider = PROVIDER_GOOGLECODE
		url = "coge.google.com/p/%s" % repo
		name = googlecode2pkgdb(url)
		commit = options.revision
		shortcommit = commit[:12]
		archive = "%s.tar.gz" % (commit)
		archive_dir = "%s-%s" % (repo, commit)
		archive_url = "https://github.com/%s/%s/archive/%s/%s" % (project, repo, commit, archive)
		parts = repo.split(".")
		lp = len(parts)
		if lp > 2:
			print "Repository name contains more than 1 dot"
			exit(1)

		if lp == 2:
			rrepo = "%s.%s" % (parts[1], parts[0])
		else:
			rrepo = repo

		archive_url = "https://%s.googlecode.com/archive/%s" % (rrepo, archive)
	else:
		provider = PROVIDER_BITBUCKET
		url = "bitbucket.org/%s/%s" % (project, repo)
		name = bitbucket2pkgdb(url)
		if options.commit == "":
			print "%sGetting the latest commit from %s%s" % (BLUE, url, ENDC)
			commit = getBitbucketLatestCommit(project, repo)
			if commit == "":
				print "%sUnable to get the latest commit%s" % (RED, ENDC)
				exit(1)
			print ""
		else:
			commit = options.commit
		shortcommit = commit[:12]
		archive = "%s.tar.gz" % (shortcommit)
		archive_dir = "%s-%s-%s" % (project, repo, shortcommit)
		archive_url = "https://bitbucket.org/%s/%s/get/%s" % (project, repo, archive)
	if name == "":
		print "Unable to generate package name for %s" % url
		exit(1)

	specfile = "%s.spec" % name
	total = 4

	# print basic information
	printBasicInfo(url, commit, name)
	print ""

	# is the package already in Fedora
	print "%s(1/%s) Checking if the package already exists in PkgDB%s" \
		% (YELLOW, total, ENDC)
	isPkgInPkgDB(name, options.force)

	# creating basic folder structure
	createBasicDirectories(name)

	# download tarball
	print "%s(2/%s) Downloading tarball%s" % (YELLOW, total, ENDC)
	downloadTarball(archive_url)
	so, se, rc = runCommand("tar -xf %s" % archive)
	if rc != 0:
		print "Unable to extract %s" % archive
		exit(1)

	# generate spec file
	print "%s(3/%s) Generating spec file%s" % (YELLOW, total, ENDC)
	spec = SpecGenerator(provider, project, repo, commit, archive_dir)
	spec.initGenerator()

	try:
		file = open("%s" % specfile, "w")
		spec.setOutputFile(file)
		err = spec.write()
		if err != "":
			print "Unable to generate spec file: %s" % err
			exit(1)
	except IOError:
		print "Error: can\'t open %s file" % specfile

	file.close()

	so, se, rc = runCommand("rpmdev-bumpspec %s -c \"First package for Fedora\"" % specfile)
	if rc != 0:
		print "Unable to bump spec file: %s" % se
		exit(1)

	print "%s(4/%s) Discovering golang dependencies%s" % (YELLOW, total, ENDC)

	ip_used = spec.getImportedPaths()

	classes = decomposeImports(ip_used)
	sorted_classes = sorted(classes.keys())

	for element in sorted_classes:
		if element == "Native":
			continue

		if element.startswith(url):
			continue

		pkg_name = repo2pkgName(element)
		pkg_in_pkgdb = False

		if pkg_name != "":
			pkg_in_pkgdb = packageInPkgdb(pkg_name)
			if pkg_in_pkgdb:
				print (GREEN + "Class: %s (%s) PkgDB=%s" + ENDC) % (element, pkg_name, pkg_in_pkgdb)
			else:
				print (RED + "Class: %s (%s) PkgDB=%s" + ENDC ) % (element, pkg_name, pkg_in_pkgdb)


	print ""
	print "%sSpec file %s at %s%s" % (YELLOW, specfile, os.getcwd(), ENDC)


