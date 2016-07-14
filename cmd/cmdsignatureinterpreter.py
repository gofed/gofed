#!/bin/python

from cmdsignatureparser import CmdSignatureParser
import os
import sys
import logging

class cmdSignatureInterpreter(object):

	def __init__(self, signature_files):
		self._cmd_signature_parser = CmdSignatureParser(signature_files)
		self._short_eval = False
		self._image = "gofed/gofed:v1.0.0"
		self._binary = "/home/gofed/gofed/hack/gofed.sh"

	def interpret(self, args):
		if "-h" in args or "--help" in args:
			self._short_eval = True
			return self

		self._cmd_signature_parser.generate().parse(args)
		if not self._cmd_signature_parser.check():
			exit(1)

		return self

	def setDefaultPaths(self, empty_path_flags, active_pos_args):
		raise NotImplementedError

	def dockerSignature(self, command):
		if self._short_eval:
			return "docker run -t %s %s %s -h" % (self._image, self._binary, command)

		flags = self._cmd_signature_parser.flags()
		options = vars(self._cmd_signature_parser.options())
		non_default_flags = []
		for flag in flags:
			if options[flags[flag]["target"]] != flags[flag]["default"]:
				non_default_flags.append(flag)

		# are there any unspecified flags with default paths?
		empty_path_flags = (set(self._cmd_signature_parser.FSDirs().keys()) - set(non_default_flags))

		# set command specific flags
		u_options, u_non_default_flags, active_pos_args = self.setDefaultPaths(empty_path_flags, self._cmd_signature_parser.full_args())

		for flag in u_non_default_flags:
			non_default_flags.append(flag)
			options[flag] = u_options[flag]

		# remap paths
		# each path is to be mapped to itself inside a container
		host_paths = []
		for flag in flags:
			if self._cmd_signature_parser.isFSDir(flags[flag]):
				path = options[flags[flag]["target"]]
				if path != "":
					host_paths.append(path)

		for arg in active_pos_args:
			if self._cmd_signature_parser.isFSDir(arg):
				host_paths.append(arg["value"])

		host_paths = list(set(host_paths))

		mounts = []
		for host_path in host_paths:
			mounts.append({
				"host": host_path,
				"container": host_path
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

		active_pos_args_str = " ".join(map(lambda l: l["value"], active_pos_args))

		return "docker run %s -t %s %s %s %s %s" % (mounts_str, self._image, self._binary, command, cmd_flags_str, active_pos_args_str)

class repo2specInterpreter(cmdSignatureInterpreter):

	def setDefaultPaths(self, empty_path_flags, active_pos_args):
		options = {}
		non_default_flags = []
		pos_args = []

		# directory option is control flag, if not set spec is generated from upstream.
		# Thus, only target option is relevant to re-mapping
		if "target" in empty_path_flags:
			options["target"] = os.getcwd()
			non_default_flags.append("target")

		return options, non_default_flags, pos_args

class inspectInterpreter(cmdSignatureInterpreter):

	def setDefaultPaths(self, empty_path_flags, pos_args):
		options = {}
		non_default_flags = []

		# only the first positional argument which if not set defaults to the current directory
		if pos_args[0]["value"] == "":
			pos_args[0]["value"] = os.getcwd()

		return options, non_default_flags, pos_args

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

if __name__ == "__main__":
	if len(sys.argv) == 1:
		logging.error("Missing command name")
		exit(1)

	cmd = sys.argv[1]

	if cmd == "repo2spec":
		cmd_dir = "repo2spec"
		signature_files = ["repo2gospec-global.yml", "repo2gospec.yml"]
		interpreter = repo2specInterpreter
	elif cmd == "inspect":
		cmd_dir = "inspect"
		signature_files = ["inspecttarball.yml"]
		interpreter = inspectInterpreter
	else:
		logging.error("Command '%s' not recognized" % cmd)
		exit(1)

	if "CMD_SIGNATURES_DIR" in os.environ:
		signature_dir = os.environ["CMD_SIGNATURES_DIR"]
	else:
		signature_dir = "%s/%s" % (getScriptDir(__file__), cmd_dir)

	print interpreter(
		map(lambda l: "%s/%s" % (signature_dir, l), signature_files),
		).interpret(sys.argv[2:]).dockerSignature(cmd)
