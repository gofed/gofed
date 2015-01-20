#!/bin/sh

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

script_dir=$(dirname $0)

function processBranch {
	fedpkg switch-branch $1
	fedpkg push
}

# get branches
branches=$(cat $script_dir/config/go2fed.conf | grep "^branches:" | cut -d':' -f2)
if [ "$branches" == "" ]; then
        branches=$(git branch --list | sed 's/\*//g' | grep -v "el6")
fi

for branch in $branches; do
	processBranch $branch
done

