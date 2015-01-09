#!/bin/sh

script_dir=$(realpath $(dirname $0))

# get packages names
packages=$(cat $script_dir/golang.packages)

# run scan
rm -f scan.log
for pkg_name in $packages; do
	echo "Scanning ${pkg_name}..."
	echo "Scanning ${pkg_name}..." >> scan.log
	$script_dir/inspectpackage.py $pkg_name -o ${pkg_name}.xml >> scan.log
	if [ $? -eq 0 ]; then
		$script_dir/xml2info.py ${pkg_name}.xml
	fi
	echo "" >> scan.log
done
