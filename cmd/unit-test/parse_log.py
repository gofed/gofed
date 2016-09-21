#!/usr/bin/python

import sys
import re
import logging
import json

MAX_ERROR_MSG_SIZE = 700

class UnitTestBuildLogError(Exception):
	pass

class TestBuildLogParser(object):

	def __init__(self):
		self._tests = {}

	def parse(self, lines):
		test_lines = []
		test_line_found = False
		summary_line = ""
		
		tests = []
		
		for line in lines:
			# end when hitting #### PASS: 10, FAILED: 0
			if line.startswith("#### PASS: "):
				summary_line = line
				break
		
			if line.startswith("go test"):
				if test_line_found:
					tests.append(test_lines)
		
				test_line_found = True
				test_lines = [line]
				continue
		
			if test_line_found:
				test_lines.append(line)
				continue
		
		tests.append(test_lines)
		
		parsed_tests = []

		for test in tests:
			test = map(lambda l: l.strip(), test)
			test = filter(lambda l: l, test)
		
			if not test:
				raise UnitTestBuildLogError("Missing test")
		
			if len(test) < 2:
				raise UnitTestBuildLogError("Missing test result")
		
			# first line is the test
			groups = re.match(r"go test (.*)", test[0])
			if not groups:
				raise UnitTestBuildLogError("Missing go test PATH line")
				continue
		
			if test[1].startswith("ok"):
				success = True
			else:
				success = False
		
			if len(test) == 2:
				error_msg = ""
			else:
				error_msg = "\n".join(test[2:])

			if len(error_msg) > MAX_ERROR_MSG_SIZE:
				error_msg = error_msg[:MAX_ERROR_MSG_SIZE]

			test_obj = {
				"package": groups.group(1),
				"success": success,
				"error_msg": error_msg
			}
		
			parsed_tests.append(test_obj)
		
		groups = re.match("#### PASS: (\d+), FAILED: (\d+)", summary_line)
		if not groups:
			raise UnitTestBuildLogError("Missing summary line")
		else:
			passed = groups.group(1)
			failed = groups.group(2)
		
		self._tests = {
			"tests": parsed_tests,
			"failed": failed,
			"passed": passed
		}

		return self

	def tests(self):
		return self._tests

if __name__ == "__main__":
	lines = sys.stdin.read().split("\n")
	parser = TestBuildLogParser().parse(lines)

	tests = parser.tests()

	#for test in tests["tests"]:
	#	if test["success"]:
	#		continue

	#	print "#### Package: %s" % test["package"]
	#	print test["error_msg"]
	#	print ""

	print json.dumps(tests)
