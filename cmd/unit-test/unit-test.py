#!/bin/python

from subprocess import PIPE, Popen, call
import os
import logging
from cmdsignature.parser import CmdSignatureParser

def runCommand(cmd):
	#cmd = cmd.split(' ')
	process = Popen(cmd, stderr=PIPE, stdout=PIPE, shell=True)
	stdout, stderr = process.communicate()
	rt = process.returncode

	return stdout, stderr, rt

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

gopath = os.environ["GOPATH"] if "GOPATH" in os.environ else "/usr/share/gocode"

def installRpm(rpm):
	rc = call("dnf install %s -y" % rpm, shell=True)
	if rc > 0:
		exit(rc)

def getTestPaths(rpm):
	so, se, rc = runCommand("rpm -ql %s" % rpm)
	if rc > 0:
		logging.error(so)
		exit(rc)

	lines = so.split("\n")[:-1]
	# only go code
	lines = filter(lambda l: l.startswith(gopath), lines)
	# only *.go files
	lines = filter(lambda l: l.endswith(".go"), lines)
	# only dirs
	lines = map(lambda l: os.path.dirname(l), lines)
	# unique the lines
	return list(set(lines))

def runTests(paths):
	gopath_prefix_len = len(gopath) + 5

	tests = {"pass": 0, "failed": 0}

	for line in paths:
		cmd = "go test %s" % line[gopath_prefix_len:]
		rc = call(cmd, shell=True)
		if rc > 0:
			tests["failed"] += 1
		else:
			tests["pass"] += 1

	print "\n#### PASS: %s, FAILED: %s" % (tests["pass"], tests["failed"])

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/unit-test.yml" % (cur_dir)

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	installRpm(options.rpm)
	paths = getTestPaths(options.rpm)
	runTests(paths)
