#!/bin/sh

# use-case
# 1) download tarball
# 2) compare tarballs
# 3) update spec file

commit=$1
spec_file="*.spec"

function getValue {
	echo $1 | sed 's/[ \t][ \t]*/ /g' | cut -d' ' -f3
}

echo "    Parsing spec file import path"
provider=$(getValue "$(cat $spec_file | grep "%global provider" | grep -v "provider_tld")")
provider_tld=$(getValue "$(cat $spec_file | grep "%global provider_tld")")
project=$(getValue "$(cat $spec_file | grep "%global project")")
repo=$(getValue "$(cat $spec_file | grep "%global repo")")

#%{provider}.%{provider_tld}/%{project}/%{repo}
import_path=$provider.$provider_tld/$project/$repo

# download tarball
echo "    Downloading tarball"
wget https://$import_path/archive/$commit/$repo-${commit:0:7}.tar.gz

# put the git hash in there
echo "    Updating spec file"
sed -i -e "s/%global commit\([[:space:]]\+\)[[:xdigit:]]\{40\}/%global commit\1$commit/" $spec_file
# increment the version number
rpmdev-bumpspec --comment="Bump to upstream ${commit}" $spec_file

echo "    Rpmlint spec file"
rpmlint $spec_file
