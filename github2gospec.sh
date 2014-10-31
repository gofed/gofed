#!/bin/sh

if [ "$#" -ne 3 ]; then
	echo "Error: Wrong number of parameters."
	echo "Synopsis: $0 PROJECT REPO COMMIT"
	exit 0
fi

project=$1
repo=$2
provider='github'
provider_tld='com'
commit=$3
shortcommit=${commit:0:7}
script_dir=$(dirname $0)

red='\e[0;31m'
orange='\e[0;33m'
NC='\e[0m'

total=4

echo -e "${orange}Repo URL:$NC"
echo "https://$provider.$provider_tld/$project/$repo"
echo ""
# prepare basic structure
name=golang-$provider-$project-$repo

echo -e "${orange}(1/$total) Checking if the package already exists in PkgDB$NC"
git ls-remote "http://pkgs.fedoraproject.org/cgit/$name.git/" 2>/dev/null 1>&2

if [ "$?" -eq 0 ]; then
	echo -e "$red\tPackage already exists$NC"
	exit 0
fi

# creating basic folder structure
mkdir -p $name/fedora/$name
cd $name/fedora/$name

echo -e "${orange}(2/$total) Creating spec file$NC"
# creating spec file
specfile=$name".spec"
echo "%global debug_package   %{nil}" > $specfile
echo "%global provider        github" >> $specfile
echo "%global provider_tld    com" >> $specfile
echo "%global project         $project" >> $specfile
echo "%global repo            $repo" >> $specfile
echo "%global import_path     %{provider}.%{provider_tld}/%{project}/%{repo}" >> $specfile
echo "%global commit          $commit" >> $specfile
echo "%global shortcommit     %(c=%{commit}; echo \${c:0:7})" >> $specfile
echo "" >> $specfile
echo "Name:           golang-%{provider}-%{project}-%{repo}" >> $specfile
echo "Version:        0" >> $specfile
echo "Release:        0.0.git%{shortcommit}%{?dist}" >> $specfile
echo "Summary:        !!!!FILL!!!!" >> $specfile
echo "License:        !!!!FILL!!!!" >> $specfile
echo "URL:            https://%{import_path}" >> $specfile
echo "Source0:        https://%{import_path}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz" >> $specfile
echo "%if 0%{?fedora} >= 19 || 0%{?rhel} >= 7" >> $specfile
echo "BuildArch:      noarch" >> $specfile
echo "%else" >> $specfile
echo "ExclusiveArch:  %{ix86} x86_64 %{arm}" >> $specfile
echo "%endif" >> $specfile
echo "" >> $specfile
echo "%description" >> $specfile
echo "%{summary}" >> $specfile
echo "" >> $specfile
echo "%package devel" >> $specfile
echo "BuildRequires:  golang >= 1.2.1-3" >> $specfile
echo "Requires:       golang >= 1.2.1-3" >> $specfile
echo "Summary:        %{summary}" >> $specfile
echo "Provides:       golang(%{import_path}) = %{version}-%{release}" >> $specfile
echo "" >> $specfile
echo "%description devel" >> $specfile
echo "%{summary}" >> $specfile
echo "" >> $specfile
echo "This package contains library source intended for " >> $specfile
echo "building other packages which use %{project}/%{repo}." >> $specfile
echo "" >> $specfile
echo "%prep" >> $specfile
echo "%setup -q -n %{repo}-%{commit}" >> $specfile
echo "" >> $specfile
echo "%build" >> $specfile
echo "" >> $specfile
echo "%install" >> $specfile
echo "install -d -p %{buildroot}/%{gopath}/src/%{import_path}/" >> $specfile
echo "cp -pav *.go %{buildroot}/%{gopath}/src/%{import_path}/" >> $specfile
echo "cp -pav !!!!FILL!!!! %{buildroot}/%{gopath}/src/%{import_path}/" >> $specfile
echo "" >> $specfile
echo "%check" >> $specfile
echo "GOPATH=%{buildroot}/%{gopath}:%{gopath} go test %{import_path}" >> $specfile
echo "" >> $specfile
echo "%files devel" >> $specfile
echo "%doc README.md LICENSE CHANGELOG.md " >> $specfile
echo "%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}" >> $specfile
echo "%dir %{gopath}/src/%{import_path}/" >> $specfile
echo "%dir %{gopath}/src/%{import_path}/!!!!FILL!!!!" >> $specfile
echo "%{gopath}/src/%{import_path}/*.go" >> $specfile
echo "" >> $specfile
echo "%changelog" >> $specfile
echo "" >> $specfile

rpmdev-bumpspec $specfile -c "First package for Fedora"

echo -e "${orange}(3/$total) Downloading tarball$NC"
download=$(wget -nv https://github.com/$project/$repo/archive/$commit/$repo-$shortcommit.tar.gz 2>&1)
if [ "$?" -ne 0 ]; then
	echo "	Unable to download the tarball"
	echo "	$download"
	exit
fi

echo -e "${orange}(4/$total) Discovering golang dependencies$NC"
tar -xf $repo-$shortcommit.tar.gz
cd $repo-$commit
$script_dir/ggi.py -c -s -d | grep -v $name

cd ..

echo ""
echo -e "${orange}Spec file $name.spec at:$NC"
pwd

