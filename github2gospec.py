import optparse
from modules.Utils import ENDC, YELLOW, RED, GREEN
from modules.Utils import runCommand
from modules.Repos import github2pkgdb
from modules.Packages import packageInPkgdb
from modules.ImportPaths import decomposeImports
from modules.Repos import repo2pkgName
from modules.specParser import SpecGenerator
import os
import errno

def setOptions():
	parser = optparse.OptionParser("%prog [-e] [-d] file [file [file ...]]")

	parser.add_option(
	    "", "-r", "--repo", dest="repo", default = "",
	    help = "Repository name, github.com/project/REPO"
	)

	parser.add_option(
	    "", "-p", "--project", dest="project", default = "",
	    help = "Project name, github.com/PROJECT/repository"
	)

	parser.add_option(
	    "", "-c", "--commit", dest="commit", default = "",
	    help = "Commit"
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

	if options.repo == "":
		print "Repository missing"
		fail = True

	if options.project == "":
		print "Project missing"
		fail = True

	if options.commit == "":
		print "Commit missing"
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

def downloadTarball(tar_url):
	so, se, rc = runCommand("wget -nv %s" % tar_url)
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

	# collect spec file information
	provider = "github"
	provider_tld = "com"
	project = options.project
	repo = options.repo
	url = "%s.%s/%s/%s" % (provider, provider_tld, project, repo)
	commit = options.commit
	shortcommit = commit[:7]

	name = github2pkgdb(url)
	if name == "":
		print "Unable to generate package name for %s provider" % provider
		exit(1)

	specfile = "%s.spec" % name
	total = 4

	# print basic information
	printBasicInfo(url, commit, name)
	print ""

	# is the package already in Fedora
	print "%s(1/%s) Checking if the package already exists in PkgDB%s" \
		% (YELLOW, total, ENDC)
	#isPkgInPkgDB(name, options.force)

	# creating basic folder structure
	createBasicDirectories(name)

	# download tarball
	print "%s(2/%s) Downloading tarball%s" % (YELLOW, total, ENDC)
	archive = "%s-%s.tar.gz" % (repo, shortcommit)
	archive_dir = "%s-%s" % (repo, commit)
	archive_url = "https://github.com/%s/%s/archive/%s/%s" % (project, repo, commit, archive)
	#downloadTarball(tar_url)
	so, se, rc = runCommand("tar -xf %s" % archive)
	if rc != 0:
		print "Unable to extract %s" % archive
		exit(1)

	# generate spec file
	print "%s(3/%s) Generating spec file%s" % (YELLOW, total, ENDC)
	spec = SpecGenerator(provider, provider_tld, project, repo, commit, archive_dir)
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


