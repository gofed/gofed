from modules.Utils import runCommand
import re
import sys

def parseOptions(command, plugin_path):
	so, se, rc = runCommand("./gofed -p %s %s --help" % (plugin_path, command))
	if rc != 0:
		return []

	options = []
	option_f = False
	for line in so.split("\n"):
		if line == "Options:":
			option_f = True
			continue

		if option_f == True:
			if line == "":
				break

			# line must start with two spaces and minus
			if len(line) < 3:
				continue

			if line[:3] != "  -":
				continue

			line = line.strip()
			parts = line.split('  ')[0].split(',')

			if parts == []:
				continue

			# do we have both short and long options?
			opts = map(lambda i: i.strip().split(' ')[0].split('=')[0], parts)
			for opt in opts:
				options.append(opt)
			
	return sorted(options)

if __name__ == "__main__":

	if len(sys.argv) != 3:
		print ""

	command = sys.argv[1]
	plugin_path = sys.argv[2]
	options = parseOptions(command, plugin_path)

	if options == []:
		print command + ":"
	else:
		print command + ":" + " ".join(options)
