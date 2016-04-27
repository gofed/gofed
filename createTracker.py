import ConfigParser
import xmlrpclib
import os
from gofed_lib.distribution.clients.pkgdb.client import PkgDBClient
import optparse

def createTracker(bugzilla, login, password, package_name):
	rpc = xmlrpclib.ServerProxy("https://%s/xmlrpc.cgi" % bugzilla)

	args = dict(
		Bugzilla_login = login,
		Bugzilla_password = password,
	)

	args["product"] = "Fedora"
	args["component"] = package_name
	args["summary"] = "Tracker for %s" % package_name
	args["description"] = "Tracker for async updates of %s for rawhide and other fedora distribution." % package_name
	args["description"] += "\n\nAs golang devel packages are used only as a build-time dependency at the moment, this tracker keeps updates and other information about this package, e.g. broken dependencies, exceptions, important pieces of information and other issues."
	args["version"] = "rawhide"
	args["status"] = "ASSIGNED"
	args["op_sys"] = "Linux"
	args["platform"] = "All"

	try:
		result = rpc.Bug.create(args)
	except xmlrpclib.Fault, e:
		print e.faultString
		exit(1)

	newBugId = int(result["id"])
	print "Created bug: https://%s/%s" % (bugzilla, newBugId)

def hasPackageTracker(bugzilla, login, password, package_name):
	rpc = xmlrpclib.ServerProxy("https://%s/xmlrpc.cgi" % bugzilla)

	args = dict(
		Bugzilla_login = login,
		Bugzilla_password = password,
		limit = 0,
		product = ['Fedora'],
		component = [package_name],
		include_fields = ['id', 'summary']
	)

	result = rpc.Bug.search(args)
	for item in result['bugs']:
		if item['summary'].startswith("Tracker for %s" % package_name):
			return True, item['id']

	return False, -1

if __name__ == "__main__":
	parser = optparse.OptionParser()

	parser.add_option(
	    "-b", "--bugzilla", dest = "bugzilla", action = "store", default = "bugzilla.redhat.com",
	    help = "Bugzilla instance to use"
	)

	parser.add_option(
	    "-p", "--package", dest = "package", action = "store", default = "",
	    help = "Package name"
	)

	options, args = parser.parse_args()

	if options.package == "":
		print "Package missing"
		exit(1)

	config = ConfigParser.ConfigParser()
	config.read(os.path.expanduser("~/.bugzillarc"))

	login = config.get(options.bugzilla, "user")
	password = config.get(options.bugzilla, "password")

	# package exists?
	if not PkgDBClient().packageExists(options.package):
		print "Unable to find %s in a list of packages" % options.package

	# does the tracker already exists?
	has, id = hasPackageTracker(options.bugzilla, login, password, options.package)
	if has:
		print "Tracker for %s already exists" % options.package
		print "https://%s/%s" % (options.bugzilla, id)
		exit(1)

	createTracker(options.bugzilla, login, password, options.package)

