## PACKAGING OF GOLANG PROJECT

Audience
* users wanting to package a golang project in Fedora
* no knowledge of golang packaging guidelines
* users wanting to package a golang project from scratch

Preliminaries
* Knowledge of Fedora packaging
* Basic knowledge of golang

If you are starting golang packager,
if you have packaged some golang packages and want to speed up you work,
if you update your spec files regurarly,
go ahead and meet gofed.

Gofed is a toolset that automates the packaging process of golang
development source codes [1].

It supports the following features:
* a spec file generator for the github.com, code.google.com, and bitbucket.org repositories
* preparation of the Fedora's Review Request for a new golang package
* golang imports discovering (dependency on other imports or packages)
* comparison of APIs (exported symbols) of two golang projects
* scan of available golang packages, construction of dependency graphs of packages
* other useful commands (parallel push, pull or update of all chosen branches, ...)

First episode of this story will show you how to package your first golang
project. It will show and explain important lines of spec line, concentrate
on macros, list of BuildRequires and Requires, list of Provides.

#### Where to get gofed

On Fedora 21 you can run:

```vim
yum install gofed
```

On Fedora 22 and higher:

```vim
dnf install gofed
```

It will install the basic tools that allows you to generated spec files from
github.com, code.google.com or bitbucket.org repository. To discover a list
of imported and provided golang packages, a list of tests.

If you want to try the latest gofed, clone its repository and alias gofed,
checkout the README.md at [1].

[1] https://github.com/ingvagabund/gofed

#### Terminology

Package and project can be used with different meaning based on a context.
If I will talk about Fedora package, word 'package' will be used.
Golang project consists of source code units called packages. In this
context, word 'golang package' will be used. The same holds for word 'project'.
If I will talk about github project, I will used word 'github project' if
it is not clear from the context. Otherwise 'project' will mean golang project.

#### Generate you first spec file

Gofed provides 3 generators:
* for github.com provider 'gofed github2spec'
* for code.google.com provider 'gofed googlecode2spec'
* for bitbucker.org provider 'gofed bitbucket2spec'

All generators can be accessed via 'gofed repo2spec' command. If you know
provider, project and repository in advance, specific generators are your
choice. E.g. for github.com/kr/pretty run:

```vim
gofed github2spec --project kr --repo pretty
```

If you have import path only and are not sure how to decode required parts
(e.g. github.com/mesos/mesos-go/auth/sasl/mech)
you can try:

```vim
gofed repo2spec --detect github.com/mesos/mesos-go/auth/sasl/mech
```

Gofed will decompose the path for you and choose the correct provider.
Unless specified, generator takes the latest commit available, downloads
tarball with source codes corresponding to the commit and generates spec file.
At the moment, commit is automatically detected for github.com and
bitbucket.org. For code.google.com/p, 'gofed googlecode2spec' is the only
choice.

In general, for code.google.com/p/REPO and REV (revision term is used instead
of commit), use:

```vim
gofed googlecode2spec --repo=REPO --rev=REV
```

#### Analysis of generated spec file

Header of each spec file starts with:

```
%if 0%{?fedora}
%global with_devel 1
%global with_bundled 0
%global with_debug 0
%global with_check 1
%global with_unit_test 1
%else
%global with_devel 0
%global with_bundled 1
%global with_debug 0
%global with_check 0
%global with_unit_test 0
%endif
```

Based on a distribution it defines that spec file will provide devel subpackage
(with_devel), binaries will be built from bundled source codes
(with_bundled), binaries will be built with debugging support (with_debug),
tests in %check section will be run (with_check) or
unit-test subpackage will be provided (with_unit_test).

Wherever you expect development from golang source codes set with_devel to 1.
This will allow other projects to include your source codes. The aim of devel
subpackage is to provide only files (at least all *.go) that are really
necesary for development (install only what you really need philoshophy).

In order to support CI testing of golang packages, unit-test subpackage is
provided. By default, it contains only *_test.go files which are needed by
golang to unit-test developed source codes. 

##### Defined macros

Before name and version of a package are set, some macros are defined:
``provider``, ``provider_tld``, ``project``, ``repo``,
``provider_prefix``, ``import_path``, ``commit`` and ``shortcommit``.
Macros ``provider`` and ``provider_tld`` are used to detect a server where the given
github project and repository are stored. Macro ``project`` and ``repo`` are remaining
two macros that together with ``provider`` and ``provider_tld`` uniquely define
server storage of the repository. Macro ``provider_prefix`` defined as it is is
used in 'Source' tag to specify a path to a repository archive file.
Macro ``import_path`` defines a prefix for every golang package provided
by a given golang project. Other golang projects can then use this prefix
to uniquely choose golang package to import. As in many cases import path
prefix inherits provider's url where project's source codes are stored,
``import_path`` macro equals ``provider_prefix``. Difference between these two
macros is to distuinguish between provider which stores source codes and
import path prefix that is used by other golang projects.

##### Correct architecture to build rpm on

Golang compiler does not support every architecture where you could possibly
build, test and run your projects. For unsupported architectures,
gcc-go compiler is an option. To cover this situtation, the following lines
in spec file are generated:

```vim
# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}
```

Macro ``go_arches`` defines a list of all architectures that are
supported by both golang and gcc-go compiler. If the macro is not defined
explicit list of architectures for golang is used. The macro is not defined
in epel6. On Fedora 21 it contains only a list of architectures supported
by golang.

The second part chooses the correct compiler. To make architectures specific
compiler transparent to user, compiler(go-compiler) virtual provide is
introduced. It installs the correct compiler on all supported architectures.
The virtual provide is defined in go-compilers package. The package also
defines ``go_compiler`` macro. If there is no go-compiler package, ``go_compiler``
is undefined and implicit compiler is used.

##### Devel subpackage

Devel subpackage is a core of every Fedora package. It provides source codes
for building other packages which use imported packages with golang project's
import path prefix. Every golang project has two types of packages: those
that are imported (by import keyword) and those that are provided
(defined by the project). For Fedora package imported packages translate into
build-time and run-time dependencies and provided packages into a list of
Provides. In the form the spec file is generated, all build-time dependencies
are wrapped with 'with_check' macro. Since it make sense to BuildRequire
golang packages only where you run some tests on the project. Run-time
dependencies are needed everytime you install the devel subpackage

All provided packages are in a form of virtual provides 'golang(package)'.
As this list of virtual provides can change with every update
(backward compatibility is not guaranted), don't forget to update your
spec file if you see build errors with missing 'golang(package)'
dependencies.

As devel subpackage ships source codes only it is marked as noarch.

Together with ``%package devel`` and ``%description devel`` section, ``%install`` section
contains installation script that copies every file with *.go suffix but not
*_test.go sufix to devel subpackage. The aim is to ship only those files
that are really needed in the devel subpackage. Other files with different
extension than *.go can be inseparable part of the source codes. For example,
files with *.s and *.proto extension could be copied to the devel subpackage
as well. Generated ``%install`` section covers only *.go files so it is up to
a packager to choose the correct files and be familiar with the golang project.

To find a list of files not ending with *.go suffix you can run the following
command in tarball's root directory:

```vim
find . \! -iname "*.go"
```

For example in tarball of github.com/golang/protobuf you can get:

```
...
./Make.protobuf
./.gitignore
./README
./AUTHORS
./proto
./proto/testdata
./proto/testdata/test.proto
./proto/testdata/Makefile
./proto/Makefile
./proto/proto3_proto
./proto/proto3_proto/proto3.proto
./src
./src/github.com
...
```

Here, proto3.proto file is a part of proto3_proto package definition which is
a candidate for devel subpackage.

##### Unit-test subpackage

For every golang project it is possible to write down unit tests. Each such
a file ends with _test.go suffix. In order to make devel subpackage as small
as possible, every unit test file belongs to unit-test subpackage. However,
as all tests need source codes to be run on, unit-test subpackage has devel
subpackage as a run-time dependency. Installation section works the same way
as for devel. Thus it is up to a packager to add other files that are needed
for testing. Test files usually contain test or testdata keyword.

Again, you can use 'find' command. For example above, test.proto is a candidate
for unit-test subpackage.

Another reason to have unit-test subpackage is a support for CI. As some tests
need internet connection, specific configuration or services running, those
tests can not be run during building. In CI, unit-test subpackage can be run
in well defined environment which support exactly those resources that are needed.

As tests are run on various architectures virtual provide is used again.
For that reason the subpackage is architecture specific.

#### Generating spec file with %build section

If you run 'gofed repo2spec' with --with-build option, build section is
generated as well. It contains heads up with ``with_debug`` and ``with_bundled``
macros wrapping building parts of golang project. For example, setting
``GOPATH`` macro or choosing to correct compiler.

#### Review request

To get a new package into Fedora, review request has to be created.
It contains basic information about the new package itself. For example,
package description, package summary, package name, spec file and source
rpm. Among other things succesfull build in Koji. The information has to be
inserted into bugzilla as a new bug.

In order to provided an easy way to generate review request, gofed tool
provides 'gofed review-request' command. Running the command in a directory containing
spec file you get:

```vim
$ gofed review-request --skip-rpmlint-errors
Parsing golang-github-onsi-gomega.spec file
  Provider: github
  Repo: gomega
  Commit: 8adf9e1730c55cdc590de7d49766cb2acc88d8f2
  Name: golang-github-onsi-gomega
  Summary: Ginkgo's Preferred Matcher Library

Copying tarball ./gomega-8adf9e1.tar.gz to /home/jchaloup/rpmbuild/SOURCES

Building spec file using rpmbuild
  /home/jchaloup/rpmbuild/SRPMS/golang-github-onsi-gomega-0-0.4.git8adf9e1.fc20.src.rpm
  /home/jchaloup/rpmbuild/RPMS/noarch/golang-github-onsi-gomega-devel-0-0.4.git8adf9e1.fc20.noarch.rpm
  /home/jchaloup/rpmbuild/RPMS/x86_64/golang-github-onsi-gomega-unit-test-0-0.4.git8adf9e1.fc20.x86_64.rpm

Running rpmlint /home/jchaloup/rpmbuild/SRPMS/golang-github-onsi-gomega-0-0.4.git8adf9e1.fc20.src.rpm /home/jchaloup/rpmbuild/RPMS/noarch/golang-github-onsi-gomega-devel-0-0.4.git8adf9e1.fc20.noarch.rpm /home/jchaloup/rpmbuild/RPMS/x86_64/golang-github-onsi-gomega-unit-test-0-0.4.git8adf9e1.fc20.x86_64.rpm
golang-github-onsi-gomega.src:144: W: macro-in-comment %{buildroot}
golang-github-onsi-gomega.src:144: W: macro-in-comment %{gopath}
golang-github-onsi-gomega.src:144: W: macro-in-comment %{import_path}
golang-github-onsi-gomega-unit-test.x86_64: E: devel-dependency golang-github-onsi-gomega-devel
3 packages and 0 specfiles checked; 1 errors, 3 warnings.

Running koji scratch build on srpm
koji build --scratch rawhide /home/jchaloup/rpmbuild/SRPMS/golang-github-onsi-gomega-0-0.4.git8adf9e1.fc20.src.rpm --nowait
  Watching rawhide build, http://koji.fedoraproject.org/koji/taskinfo?taskID=10705051
koji watch-task 10705051 --quiet
Uploading srpm and spec file to @fedorapeople.org
jchaloup@fedorapeople.org "mkdir -p public_html/reviews/golang-github-onsi-gomega"
scp /home/jchaloup/rpmbuild/SRPMS/golang-github-onsi-gomega-0-0.4.git8adf9e1.fc20.src.rpm jchaloup@fedorapeople.org:public_html/reviews/golang-github-onsi-gomega/.
scp golang-github-onsi-gomega.spec jchaloup@fedorapeople.org:public_html/reviews/golang-github-onsi-gomega/.


Generating Review Request
###############################################################
Review Request: golang-github-onsi-gomega - Ginkgo's Preferred Matcher Library
###############################################################
Spec URL: https://jchaloup.fedorapeople.org/reviews/golang-github-onsi-gomega/golang-github-onsi-gomega.spec

SRPM URL: https://jchaloup.fedorapeople.org/reviews/golang-github-onsi-gomega/golang-github-onsi-gomega-0-0.4.git8adf9e1.fc20.src.rpm

Description: Ginkgo's Preferred Matcher Library

Fedora Account System Username: jchaloup

Koji: http://koji.fedoraproject.org/koji/taskinfo?taskID=10705051

$ rpmlint golang-github-onsi-gomega-0-0.4.git8adf9e1.fc20.src.rpm golang-github-onsi-gomega-devel-0-0.4.git8adf9e1.fc20.noarch.rpm golang-github-onsi-gomega-unit-test-0-0.4.git8adf9e1.fc20.x86_64.rpm
golang-github-onsi-gomega.src:144: W: macro-in-comment %{buildroot}
golang-github-onsi-gomega.src:144: W: macro-in-comment %{gopath}
golang-github-onsi-gomega.src:144: W: macro-in-comment %{import_path}
golang-github-onsi-gomega-unit-test.x86_64: E: devel-dependency golang-github-onsi-gomega-devel
3 packages and 0 specfiles checked; 1 errors, 3 warnings.

###############################################################


Enter values at: https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&format=fedora-review
```

The command uses 'scp' to copy files into your fedorapeople.org account.
Thus it is supposed you don't have to type your password.
Use 'ssh-copy-id' for this case.
To choose the correct FAS username, use --user option or update fasuser
in /etc/gofed.conf configuration file.

If you run the command with ``--create-review`` option,
the review request is generated in https://bugzilla.redhat.com as well.
