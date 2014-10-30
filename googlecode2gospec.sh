#!/bin/sh

if [ "$#" -ne 2 ]; then
	echo "Error: Wrong number of parameters."
	echo "Synopsis: $0 REPO REVISION"
	exit 0
fi

repo=$1
rrepo=$repo
nd=$(echo -n $repo | sed 's/[^.]//g' | wc -c)
if [ "$nd" -eq 1 ]; then
	rrepo="$(echo $repo | cut -d'.' -f2).$(echo $repo | cut -d'.' -f1)"
elif [ "$nd" -ge 2 ]; then
	echo "More then 1 dot in the repo name"
	exit
fi

provider='google'
provider_sub='code'
provider_tld='com'
rev=$2
shortrev=${rev:0:12}
script_dir=$(dirname $0)

echo "URL of the repo:"
echo "	https://$provider_sub.$provider.$provider_tld/p/$rrepo"
echo ""

# prepare basic structure
name=golang-$provider$provider_sub-$repo

echo "Checking if the package already exists in PkgDB"
#fedpkg clone $name
#if [ "$?" -eq 0 ]; then
#	echo "	Package already exists"
#	exit 0
#fi
echo ""

# creating basic folder strucure
mkdir -p $name/fedora/$name
cd $name/fedora/$name

echo "Creating spec file"
# creating spec file
specfile=$name".spec"
echo "	$specfile"
echo "%global debug_package   %{nil}" > $specfile
echo "%global provider        google" >> $specfile
echo "%global provider_sub    code" >> $specfile
echo "%global provider_tld    com" >> $specfile
echo "%global project         p" >> $specfile
echo "%global repo            $rrepo" >> $specfile
echo "%global import_path     %{provider_sub}%{provider}.%{provider_tld}/%{project}/%{repo}" >> $specfile
echo "%global rev             $rev" >> $specfile
echo "%global shortrev        %(r=%{rew}; echo \${r:0:12})" >> $specfile
echo "" >> $specfile
echo "Name:           golang-%{provider}%{provider_sub}-%{repo}" >> $specfile
echo "Version:        0" >> $specfile
echo "Release:        0.0.hg%{shortrev}%{?dist}" >> $specfile
echo "Summary:        !!!!FILL!!!!" >> $specfile
echo "License:        !!!!FILL!!!!" >> $specfile
echo "URL:            https://%{import_path}" >> $specfile
echo "Source0:        https://$repo.%{provider}%{provider_sub}.%{provider_tld}/archive/%{rev}.tar.gz" >> $specfile
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
echo "%setup -q -n %{repo}-%{shortrev}" >> $specfile
echo "" >> $specfile
echo "%build" >> $specfile
echo "" >> $specfile
echo "%install" >> $specfile
echo "install -d -p %{buildroot}/%{gopath}/src/%{import_path}/" >> $specfile
echo "cp -pav *.go %{buildroot}/%{gopath}/src/%{import_path}/" >> $specfile
echo "cp -pav !!!!FILL!!!! %{buildroot}/%{gopath}/src/%{import_path}/" >> $specfile
echo "for d in !!!!FILL DIRS TO COPY!!!!; do" >> $specfile
echo "   cp -pav $d %{buildroot}/%{gopath}/src/%{import_path}/" >> $specfile
echo "done" >> $specfile
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

echo ""

echo "Downloading tarball"
wget https://$repo.$provider$provider_sub.$provider_tld/archive/$rev.tar.gz --no-check-certificate
echo ""

echo "Inspecting golang"
tar -xf $rev.tar.gz | grep -v "in the future"
cd $repo-$shortrev
$script_dir/ggi.py
echo ""

cd ..
echo "Directory containting the spec file"
echo "	$(pwd)"


