#!/bin/python

# ####################################################################
# go2fed - set of tools to automize packaging of golang devel codes
# Copyright (C) 2014  Jan Chaloupka, jchaloup@redhat.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# ####################################################################

import os
import optparse

directory = "/home/jchaloup/Packages/golang-github-influxdb-influxdb/fedora/golang-github-influxdb-influxdb/influxdb-67f9869b82672b62c1200adaf21179565c5b75c3"
directory = "/home/jchaloup/Packages/golang-googlecode-gcfg/fedora/golang-googlecode-gcfg/gcfg-c2d3050044d0"

def getGoDirs(directory, test = False):
	go_dirs = []
	for dirName, subdirList, fileList in os.walk(directory):
		# does the dirName contains *.go files
		nogo = True
		for fname in fileList:
			# find any *.go file
			if test == False and fname.endswith(".go"):
				nogo = False
				break
			elif test == True and fname.endswith("_test.go"):
				nogo = False
				break

		if nogo:
			continue

		relative_path = os.path.relpath(dirName, directory)
		go_dirs.append(relative_path)

	return go_dirs	

def getSubdirs(directory):
	return [name for name in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, name))]

if __name__ == "__main__":

	parser = optparse.OptionParser("%prog [-p] [-d] [-t] [directory]")

	parser.add_option_group( optparse.OptionGroup(parser, "directory", "Directory to inspect. If empty, current directory is used.") )

	parser.add_option(
	    "", "-p", "--provides", dest="provides", action = "store_true", default = False,
	    help = "Display all directories with *.go files"
	)

	parser.add_option(
            "", "-d", "--dirs", dest="dirs", action = "store_true", default = False,
            help = "Display all direct directories"
        )

	parser.add_option(
	    "", "-t", "--test", dest="test", action = "store_true", default = False,
	    help = "Display all directories containing *.go test files"
	)

	options, args = parser.parse_args()

	path = "."
	if len(args):
		path = args[0]

	if options.provides:
		for dir in getGoDirs(path):
			print dir
	elif options.test:
		for dir in getGoDirs(path, test = True):
			print dir
	elif options.dirs:
		for dir in getSubdirs(path):
			print dir
	else:
		print "Usage: inspecttarball.py [-p] [-d] [-t] [directory]"
