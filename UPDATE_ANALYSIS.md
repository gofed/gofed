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
$
$ gofed bump
Searching for spec file
Reading macros from golang-github-onsi-ginkgo.spec
Getting the latest commit from github.com/onsi/ginkgo
Tags: v1.2.0-beta, v1.2.0, v1.1.1, v1.1.0, v1.0.0
Releases: 
Downloading tarball
Updating spec file
Bumping spec file
$
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
$
$ gofed lint -a ginkgo-d94e2f4.tar
...
W: Missing BuildRequires: golang(github.com/onsi/B)
W: Missing BuildRequires: golang(github.com/onsi/C)
W: Missing BuildRequires: golang(github.com/onsi/gomega/gbytes)
...
1 golang specfile checked; 1 errors, 23 warnings.
$
$ fedpkg prep
$ cd ginkgo-d94e2f4000332f62b356ecb2840c98f4218f5358
$
$ # get a list of all provided packages in a spec file format
$ gofed inspect -p --spec
Provides: golang(%{import_path}) = %{version}-%{release}
Provides: golang(%{import_path}/config) = %{version}-%{release}
Provides: golang(%{import_path}/ginkgo/convert) = %{version}-%{release}
Provides: golang(%{import_path}/ginkgo/interrupthandler) = %{version}-%{release}
...
$
$ # get a list of all imported packages in a spec file format
$ gofed ggi --spec
BuildRequires: golang(github.com/onsi/B)
BuildRequires: golang(github.com/onsi/C)
BuildRequires: golang(github.com/onsi/ginkgo)
BuildRequires: golang(github.com/onsi/ginkgo/config)
...
$
$ # get a list of all unit-tests
$ $ gofed inspect -t --spec
go test %{import_path}/ginkgo/nodot
go test %{import_path}/ginkgo/testsuite
go test %{import_path}/integration
...
```

### gofed bump

As described in the previous section, 'gofed bump' downloads a tarball
and bump the spec file. How it works?

First, spec file of a packages is parsed. Thus the command has to be run in
a package root directory. Standard golang spec file macros are detected
(provider_prefix/import_path and commit). Provider repository is detected,
list of available commits retrieved from the repository and if there is a new
commit, url for downloading tarball is constructed and tarball is downloaded.
Among others a list of tags and releases is retrieved as well. So you can
detect if there is a new version of the project. As version tag is not updated
it has to be updated manually. Finally, spec file is bumped by running
'rpmdev-bumpspec' with appropriate comment. It the last comment in %changelog
contains 'resolves: #bugid' or 'related: #bugid', 'related: #bugid' is appended
to the new comment.

As automatic detection of the latest commit is available only for github.com
and bitbucket.org, for code.google.com the commit has to be specified
explicitely (--commit option).

### gofed lint

With each update to the newest commit a list of provided and imported packages
can change. In order to automatically detect which packages are no longer
provider or imported or which are new, 'gofed lint' command can be run to check
the current list of Provides and [Build]Requires with those in the new tarball.
If you run 'gofed lint' without any arguments it expects a tarball, spec file
and sources files in the current directory. Otherwise additional options has to
be provided.

The command is meant to be run in a package root directory. The output is
mainly informative. Some golang projects can provide more packages. Some can
BuildRequire less. It is up to a maitainer to decide which warnings are legit.

### gofed inspect and gofed ggi

Each golang project is defined by a set of packages. Each package can import
one or more other packages. In order to have a fast and clean way to get
a list of all provided packages, 'gofed inspect' command is provided.
To get a list of imported packages, 'gofed ggi' command is provided.

Both commands are built over golang parser which is provided by golang
compiler itself. Extracted information about each source code are put
together (based on the golang language specification). These information
can be then used and processed in a various way.

Basic use of 'gofed inspect' and 'gofed ggi' is with --spec option. All
displayed information correspond to source codes in the current directory.
Running 'gofed inspect' with -p option will list all provided packages,
running with -t option will list all unit-test files. 'gofed ggi' command
show only imported packages that correspond to devel source codes. It does
not list packages that are imported in main packages (source codes with
'package main' language construct). If you want to see every import, run
the command with --all-occurrences option. To get a position of each import,
use --show-occurrence option as well. E.g.

```vim
$ gofed ggi --show-occurrence
	github.com/onsi/B                (integration/_fixtures/watch_fixtures/A/A.go:A)
	github.com/onsi/C                (integration/_fixtures/watch_fixtures/D/D.go:D)
	github.com/onsi/ginkgo           (types/types_test.go:types_test)
	github.com/onsi/ginkgo/config    (ginkgo_dsl.go:ginkgo)
	...
```

### Are all imported packages up-to-date?

For some golang projects it is not enough just to update tarball. Sometimes its
dependencies has to be updated as well as all dependencies are debundled into
self-standing Fedora packages. Releases of other projects can be bug fixes only.

Gofed provides two commands to check if some dependencies need to be updated.
If a tarball of a golang project ships Godeps directory it contains Godeps.json
file. The file contains a list of imported packages with its corresponding
commit in json:

```vim
{
        "ImportPath": "github.com/coreos/etcd",
        "GoVersion": "go1.4.1",
        "Packages": [
                "./..."
        ],
        "Deps": [
                {
                        "ImportPath": "bitbucket.org/ww/goautoneg",
                        "Comment": "null-5",
                        "Rev": "75cd24fc2f2c2a2088577d12123ddee5f54e0675"
                },
                {
                        "ImportPath": "github.com/beorn7/perks/quantile",
                        "Rev": "b965b613227fddccbfffe13eae360ed3fa822f8d"
                },
                {
                        "ImportPath": "github.com/bgentry/speakeasy",
                        "Rev": "5dfe43257d1f86b96484e760f2f0c4e2559089c7"
                },
...
```

Thus it is easy to check. For this case 'gofed check-deps' exists. Just
run the command in a directory containing the file.

For example, for etcd-2.1.1 you can run:
```vim
$ cd etcd-2.1.1/Godeps
$ ls
Godeps.json  Readme  _workspace
$ gofed check-deps -v
package golang-bitbucket-ww-goautoneg up2date
package golang-github-beorn7-perks up2date
import path github.com/bgentry/speakeasy not found
package golang-github-boltdb-bolt has newer commit
import path github.com/bradfitz/http2 not found
package golang-github-codegangsta-cli has newer commit
package golang-github-coreos-go-etcd outdated
package golang-github-coreos-go-semver up2date
import path github.com/coreos/pkg/capnslog not found
package golang-googlecode-gogoprotobuf has newer commit
package golang-github-golang-glog up2date
package golang-googlecode-goprotobuf has newer commit
import path github.com/google/btree not found
package golang-github-jonboulle-clockwork has newer commit
package golang-github-matttproud-golang_protobuf_extensions up2date
package golang-github-prometheus-client_golang has newer commit
package golang-github-prometheus-client_model up2date
package golang-github-prometheus-procfs has newer commit
package golang-github-stretchr-testify has newer commit
import path github.com/ugorji/go/codec not found
package golang-googlecode-go-crypto not found in golang.repos
package golang-googlecode-go-crypto not found in golang.repos
package golang-googlecode-net has newer commit
package golang-googlecode-goauth2 has newer commit
package golang-google-golangorg-cloud outdated
import path google.golang.org/grpc not found

```

Each line corresponds to a package providing imported packages or a line
corresponding to a imported package that was not found.

Other golang projects can have their own way of storing this information. Other
has no such a list. For this case 'gofed ggi -d' can provide some information.

```vim
$ cd etcd-2.1.1
$ gofed ggi -cd -v
Class: github.com/bgentry/speakeasy (golang-github-bgentry-speakeasy) PkgDB=True
Class: github.com/boltdb/bolt (golang-github-boltdb-bolt) PkgDB=True
Class: github.com/coreos/etcd (etcd) PkgDB=True
Class: github.com/coreos/go-etcd (golang-github-coreos-go-etcd) PkgDB=True
Class: github.com/coreos/go-semver (golang-github-coreos-go-semver) PkgDB=True
Class: github.com/coreos/pkg (golang-github-coreos-pkg) PkgDB=True
Class: github.com/gogo/protobuf (golang-github-gogo-protobuf) PkgDB=False
Class: github.com/google/btree (golang-github-google-btree) PkgDB=True
Class: github.com/jonboulle/clockwork (golang-github-jonboulle-clockwork) PkgDB=True
Class: github.com/prometheus/client_golang (golang-github-prometheus-client_golang) PkgDB=True
Class: github.com/prometheus/procfs (golang-github-prometheus-procfs) PkgDB=True
Class: github.com/stretchr/testify (golang-github-stretchr-testify) PkgDB=True
Class: golang.org/x/crypto (golang-googlecode-crypto) PkgDB=False
Class: google.golang.org/grpc (golang-github-grpc-grpc-go) PkgDB=True
```

Difference between both is that 'gofed check-deps' has precise commit for each
dependency. Thus it is recommended to include Godeps.json file in %doc tag in
%files devel section. On the other hand, 'gofed ggi' does not know the commit
and just checks if the given import path has package in PkgDB providing it.


