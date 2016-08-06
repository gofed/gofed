#!/bin/python

from cmdsignatureparser import CmdSignatureParser
import os
import sys
import logging
import uuid
import json

class SignatureException(Exception):
	pass

class cmdSignatureInterpreter(object):

	def __init__(self, signature_files):
		self._cmd_signature_parser = CmdSignatureParser(signature_files)
		self._short_eval = False
		self._task = "gofed"
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
		options = {}
		non_default_flags = []

		# any default actions for flags?
		flags = self._cmd_signature_parser.flags()
		for flag in empty_path_flags:
			if "default-action" not in flags[flag]:
				continue

			if flags[flag]["default-action"] == "set-cwd":
				options[flag] = os.getcwd()
				non_default_flags.append(flag)
				continue

		# any default actions for args?
		for pos_arg in active_pos_args:
			if "default-action" not in pos_arg:
				continue

			if pos_arg["default-action"] == "set-cwd":
				pos_arg["value"] = os.getcwd()
				continue

		# check there is no blank argument followed by non-empty one
		blank = False
		for i, pos_arg in enumerate(active_pos_args):
			if pos_arg["value"] == "":
				blank = True
				continue

			if blank:
				logging.error("Empty positional argument is followed by non-empty argument %s" %  pos_arg["name"])
				exit(1)

		return options, non_default_flags, active_pos_args

	def kubeSignature(self, command):
		if self._short_eval:
			raise SignatureException("kubernetes signature: help not supported")

		# get a list of arguments
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

		cmd_flags = []
		out_flags = []
		for flag in non_default_flags:
			if not self._cmd_signature_parser.isFSDir(flags[flag]):
				type = flags[flag]["type"]
				if type == "boolean":
					cmd_flags.append("--%s" % flags[flag]["long"])
				else:
					cmd_flags.append("--%s %s" % (flags[flag]["long"], options[flags[flag]["target"]]))

				continue

			# All host path arguments must have direction field
			if "direction" not in flags[flag]:
				raise SignatureException("Missing direction for '%s' flag" % flag)

			# All out arguments are mapped 1:1
			if flags[flag]["direction"] == "out":
				# change target directory to non-existent one inside a container
				# generate temporary directory in postStart
				cmd_flags.append("--%s /tmp/var/run/ichiba/%s" % (flags[flag]["long"], flag))
				out_flags.append(flag)
			else:
				raise SignatureException("Host path flags with in direction are not supported")

		# TODO(jchaloup): host paths arguments are not currently fully supported
		# - input host paths are not supported currently (later, Ichiba client (or other client) must archive and upload any input to publicly available place)
		# - only input host files are, each such file must be archive (tar.gz only for start)
		# - content of each output host path is archived and uploaded to a publicly available place (if set, tar.gz if set)
		# - archiving and uploading is part of the job as well (postStop lifecycle specification)
		# - thus, all host paths arguments carry information about their direction

		# are there any unspecified flags with default paths?
		#empty_path_flags = (set(self._cmd_signature_parser.FSDirs().keys()) - set(non_default_flags))

		task_name = "job-%s-%s-%s" % (self._task, command, uuid.uuid4().hex)

		job_spec = {
			"apiVersion": "batch/v1",
			"kind": "Job",
			"metadata": {
				"name": task_name
			},
			"spec": {
				"template": {
					"metadata": {
						"name": task_name
					},
					"spec": {
						"containers": [{
							"name": task_name,
							"image": self._image,
							"command": [
								"sudo",
								"--user=gofed",
								self._binary
							]
						}],
						# OnFailure
						"restartPolicy": "Never"
					}
				}
			}
		}

		# Add command specific flags
		for flag in cmd_flags:
			job_spec["spec"]["template"]["spec"]["containers"][0]["command"].append(flag)

		if out_flags != []:
			# add postStart script to generate anonymous paths for output host paths
			# no matter what is inside a given directory (one or more files),
			# entire directory gets archived at the end
			cmds = []
			for flag in out_flags:
				# archive all out host paths
				cmds.append("mkdir -p /tmp/var/run/ichiba/%s" % flag)

			postStartCommand = {
				"exec": {
					"command": [
						"/bin/sh",
						"-ec",
						" && ".join(cmds)
					]
				}
			}

			# add preStop script to upload generated resources
			cmds = []
			for flag in out_flags:
				# archive all out host paths
				filename = flags[flag]["target"]
				# TODO(jchaloup): how to generate unique filenames for generated resources?
				cmds.append("tar -czf %s.tar.gz /tmp/var/run/ichiba/%s" % (filename, flag))
				# TODO(jchaloup): support other storage resources
				cmds.append("scp -i /etc/storagePK %s.tar.gz ichiba@storage:/var/run/ichiba/%s/." % (filename, task_name))
				# TODO(jchaloup): collect container logs (meantime without logs)

			preStopCommand = {
				"exec": {
					"command": [
						"/bin/sh",
						"-ec",
						" && ".join(cmds)
					]
				}
			}

			job_spec["spec"]["template"]["spec"]["containers"][0]["lifecycle"] = {
				"preStop": preStopCommand,
				"postStart": postStartCommand
			}

			# create volume from secret with storage PK
			job_spec["spec"]["template"]["spec"]["volumes"] = [{
				"name": "storagePK",
				"secret": {
					"secretName": "storagePK"
				}
			}]

			job_spec["spec"]["template"]["spec"]["containers"][0]["volumeMounts"] = [{
				"name": "storagePK",
				"mountPath": "/etc/storagePK",
				"readOnly": True
			}]

		# One must assume the generated specification is publicly available.
		# Location of the private PK is known in advance.
		# For that reason, all the jobs are meant to be used privately.
		# At the same time, all jobs are uploaded to kubernetes without any authentication or authorization.
		# TODO(jchaloup): generate the job specifications inside running container in kubernetes cluster.
		# For that reason, the container will have to clone entire ichiba repository to get a list of all supported tasks.
		# Ichiba client will then just send the command signature.
		return json.dumps(job_spec)

	def jenkinsSignature(self, command):
		pass

	def vagrantSignature(self, command):
		pass

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
	pass

class inspectInterpreter(cmdSignatureInterpreter):
	pass

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
