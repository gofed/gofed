#!/bin/sh

script_dir=$(dirname $0)

for file in $@; do

	imports=$($script_dir/getimports.py $file)

	#echo "##file: $file"
	for import in $imports; do
		# filter out local named imports
		if [ "$import" == "." ]; then
			continue
		fi
		nonquota=$(echo $import | grep '"')
		if [ "$nonquota" == "" ]; then
                        continue
                fi
		echo $import
	done
	#echo "##"
	#echo "##"
done | sort -u

