## UPDATES AND ANALYSIS OF GOLANG SOURCE CODES

The second episode of the series will show you how to:
- update golang project packaged in Fedora
- analyse source codes and get list of provided and imported packages
- get a list of unit-test files

### Update of spec files

In the previous episode I showed you how to generated spec file for a given
golang project. Here, I will show you how to update packaged project with
new tarball, how to update a list of provided and imported packages and how
to update a list of unit-test files. Among others, 'gofed lint' command will
be introduced.

Every fedora package has a root directory. It is the one you cd in once you
clone its repository. For example, for golang-github-onsi-ginkgo:

```vim
$ fedpkg clone golang-github-onsi-ginkgo
$ cd golang-github-onsi-ginkgo
$ ls
golang-github-onsi-ginkgo.spec  sources
```

It contains spec file and sources file. If you run 'fedpkg prep', tarball
with source codes is downloaded as well.

Gofed provides 'gofed bump' command which allows you to automatically
download tarball of the latest commit (or the one specified via --commit
option) of a given golang project and update spec file.
The command does not update a list of provided and imported packages
nor a list of unit-tests. At the moment 'gofed bump' supports only github.com
and bitbucket.org providers.

List of provided/imported packages and unit-test has to be updated manually.
Gofed provides 'gofed inspect' and 'gofed ggi' for this case. Running the
command with --spec option will generate an output in a spec file format.

Once you run 'gofed bump' command you can run 'gofed lint' to check which
provided/required/buildrequired packages are missing or superfluous. Both
commands have to be run in a package root directory, 'gofed lint' needs a
tarball in addition to spec file and sources file.

```
$ cd golang-github-onsi-ginkgo
$ git checkout master
$ ls
ginkgo-462326b.tar.gz  golang-github-onsi-ginkgo.spec  sources
$ gofed bump
Searching for spec file
Reading macros from golang-github-onsi-ginkgo.spec
Getting the latest commit from github.com/onsi/ginkgo
Tags: v1.2.0-beta, v1.2.0, v1.1.1, v1.1.0, v1.0.0
Releases: 
Downloading tarball
Updating spec file
Bumping spec file
$ git diff
diff --git a/golang-github-onsi-ginkgo.spec b/golang-github-onsi-ginkgo.spec
index 6a3d878..62b93b2 100644
--- a/golang-github-onsi-ginkgo.spec
+++ b/golang-github-onsi-ginkgo.spec
@@ -2,7 +2,7 @@
 %global provider_tld   com
 %global project                onsi
 %global repo           ginkgo
-%global commit         462326b1628e124b23f42e87a8f2750e3c4e2d24
+%global commit         d94e2f4000332f62b356ecb2840c98f4218f5358
 # https://github.com/onsi/ginkgo
 %global import_path    %{provider}.%{provider_tld}/%{project}/%{repo}
 %global shortcommit    %(c=%{commit}; echo ${c:0:7})
@@ -10,7 +10,7 @@
 
 Name:          golang-%{provider}-%{project}-%{repo}
 Version:       1.1.0
-Release:       3%{?dist}
+Release:       4%{?dist}
 Summary:       A Golang BDD Testing Framework
 License:       MIT
 URL:           http://%{import_path}
@@ -77,6 +77,9 @@ cp -pav {config,ginkgo,integration,internal,reporters,types} %{buildroot}
 %{gopath}/src/%{import_path}
 
 %changelog
+* Fri Aug 14 2015 jchaloup <jchaloup@redhat.com> - 1.1.0-4
+- Bump to upstream d94e2f4000332f62b356ecb2840c98f4218f5358
+
 * Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.0-3
 - Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild
$ gofed lint -a ginkgo-d94e2f4.tar
...
W: Missing BuildRequires: golang(github.com/onsi/B)
W: Missing BuildRequires: golang(github.com/onsi/C)
W: Missing BuildRequires: golang(github.com/onsi/gomega/gbytes)
...
1 golang specfile checked; 1 errors, 23 warnings.
$ fedpkg prep
$ cd ginkgo-d94e2f4000332f62b356ecb2840c98f4218f5358
$ # get a list of all provided packages in a spec file format
$ gofed inspect -p --spec
Provides: golang(%{import_path}) = %{version}-%{release}
Provides: golang(%{import_path}/config) = %{version}-%{release}
Provides: golang(%{import_path}/ginkgo/convert) = %{version}-%{release}
Provides: golang(%{import_path}/ginkgo/interrupthandler) = %{version}-%{release}
...
$ # get a list of all imported packages in a spec file format
$ gofed ggi --spec
BuildRequires: golang(github.com/onsi/B)
BuildRequires: golang(github.com/onsi/C)
BuildRequires: golang(github.com/onsi/ginkgo)
BuildRequires: golang(github.com/onsi/ginkgo/config)
...
$ # get a list of all unit-tests
$ $ gofed inspect -t --spec
go test %{import_path}/ginkgo/nodot
go test %{import_path}/ginkgo/testsuite
go test %{import_path}/integration
...
```
