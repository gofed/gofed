#!/bin/python

from cmdsignatureparser import CmdSignatureParser
import os
import sys
import logging

class repo2gospecInterpreter(object):

	def __init__(self, signature_files):
		self._cmd_signature_parser = CmdSignatureParser(signature_files)

	def interpret(self, args):
		self._cmd_signature_parser.generate().parse(args)
		if not self._cmd_signature_parser.check():
			exit(1)

		return self

	def dockerSignature(self):
		flags = self._cmd_signature_parser.flags()
		options = vars(self._cmd_signature_parser.options())
		non_default_flags = []
		for flag in flags:
			if options[flags[flag]["target"]] != flags[flag]["default"]:
				non_default_flags.append(flag)

			#print (flags[flag]["target"], options[flags[flag]["target"]], flags[flag]["default"])

		# are there any unspecified flags with default paths?
		empty_path_flags = (set(self._cmd_signature_parser.FSDirs().keys()) - set(non_default_flags))
		# directory option is control flag, if not set spec is generated from upstream.
		# Thus, only target option is relevant to re-mapping
		if "target" in empty_path_flags:
			options["target"] = os.getcwd()
			non_default_flags.append("target")

		# remap paths
		# each path is to be mapped to itself inside a container
		mounts = []
		for flag in flags:
			if self._cmd_signature_parser.isFSDir(flags[flag]):
				path = options[flags[flag]["target"]]
				if path != "":
					mounts.append({
						"host": path,
						"container": path
					})

		mounts_str = " ".join(map(lambda l: "-v %s:%s" % (l["host"], l["container"]), mounts))

		cmd_flags = []
		for flag in non_default_flags:
			type = flags[flag]["type"]
			if type == "boolean":
				cmd_flags.append("--%s" % flags[flag]["long"])
			else:
				cmd_flags.append("--%s %s" % (flags[flag]["long"], options[flags[flag]["target"]]))

		cmd_flags_str = " ".join(cmd_flags)

		return "docker run %s -t gofed/gofed:v1.0.0 /home/gofed/gofed/hack/gofed.sh repo2spec %s" % (mounts_str, cmd_flags_str)

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

if __name__ == "__main__":
	if len(sys.argv) == 1:
		logging.error("Missing command name")
		exit(1)

	cmd = sys.argv[1]

	if cmd == "repo2gospec":
		if "CMD_SIGNATURES_DIR" in os.environ:
			signature_dir = os.environ["CMD_SIGNATURES_DIR"]
		else:
			signature_dir = "%s/repo2gospec" % getScriptDir(__file__)

		signature_files = [
			"%s/repo2gospec-global.yml" % signature_dir,
			"%s/repo2gospec.yml" % signature_dir
		]

		print repo2gospecInterpreter(signature_files).interpret(sys.argv[2:]).dockerSignature()	
