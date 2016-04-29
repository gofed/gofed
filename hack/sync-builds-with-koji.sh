TMP_DIR=$(mktemp -d)

pushd ${TMP_DIR} > /dev/null
echo "Temporary dir created: ${TMP_DIR}"
mkdir rpms

for package in $(cat /var/lib/gofed/data/golang.packages); do
	# remove all rpms
	rm -rf *.rpm

	# get nvr
	nvr=$(koji -q latest-pkg rawhide ${package} | cut -d' ' -f1)
	if [ -z ${nvr} ]; then
		echo "Warning: ${package} not found"
		echo ""
		continue
	fi

	# get builds
	echo "koji download-build ${nvr}"
	koji download-build ${nvr}
	if [ "$?" -ne 0 ]; then
		echo "Warning: unable to download ${nvr}"
		echo ""
		continue
	fi

	# install all devel builds
	for file in *.rpm; do
		ver=$(echo ${nvr} | rev | cut -d'-' -f2 | rev)
		rel=$(echo ${nvr} | rev | cut -d'-' -f1 | rev)
		name=$(echo ${file} | rev | cut -d'-' -f3- | rev | grep "devel$")
		if [ -z ${name} ]; then
			continue
		fi
		arch=$(uname -m)
		echo ""
		if [ -f ${name}-${ver}-${rel}.${arch}.rpm ]; then
			echo ${name}-${ver}-${rel}.${arch}.rpm
			mv ${name}-${ver}-${rel}.${arch}.rpm rpms/.
		fi
		if [ -f ${name}-${ver}-${rel}.noarch.rpm ]; then
			echo ${name}-${ver}-${rel}.noarch.rpm
			mv ${name}-${ver}-${rel}.noarch.rpm rpms/.
		fi
	done

	# you can get very fast out of memory in /tmp
	CAP=$(df | grep "/tmp" | sed "s/[ \t][ \t]*/ /g" | cut -d" " -f 5 | sed "s/%//")
	echo ""
	echo "/tmp capacity: ${CAP}%"
	if [[ ${CAP} -gt 60 ]]; then
		"GAME OVER: /tmp is more then ${CAP}% full"
		break
	fi
	echo ""
done

popd > /dev/null

echo "All rpms saved in ${TMP_DIR}"
