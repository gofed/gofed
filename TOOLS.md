##Use cases [DRAFT]

#####API of Golang projects

Each golang project corresponds to a set of source codes in golang. Each set consists of symbols like functions, methods, data types, constants or variables. Source codes (symbols) are divided into source code units called packages. A so called exported symbols are those symbols that are visible to other projects. Exported symbols starts with a capital letter and creates project's API.

When new version of a project is released (major or minor version bump, new commit), API is modified. In order to find out which symbols has been changed or removed, each exported symbol from each package of a project has to compared to its equivalent. If any exported symbol is modified (type of function's parameter is changed, number of parameters is changed, etc.), backward compatibility is broken.

Gofed tool supports comparison of two APIs. Run 'gofed abidiff --help'.

#####Fedora spec file generator

A spec file defines all the commands and values that are required for creating a package (Chapter 9. Working with Spec Files, [1]). All spec files corresponding to golang packages share the same structure. Devel subpackages provides only source codes, no binaries. If a package corresponds to a tool (kubernetes, etcd, hugo, etc.) main subpackage provides binaries. Projects come from various repositories (github.com, code.google.com, bitbucket.org,  etc.).
 
 In Fedora one spec file corresponds to one package. In order to get a package to Fedora,  review request has to be created. Each spec file then goes through review (fedora-review, rpmlint, etc.). Among other checks golang specific checks are made, i.e. check for list of provides, list of buildtime and runtime requirements, etc. Or metainformation, i.e. commit, repository, project, tarball, etc.
 
 Gofed tool can generate a spec file containing minimal required information that can be built right away. It supports github.com, code.google.com and bitbucket.org repositores. To generate a spec file you can run 'gofed github2spec', 'gofed googlecode2spec' and 'gofed bitbucket2spec'.
 
 Generated spec still need to be manually investigated. Some projects bundle dependencies in Godeps directory and import them as packages belonging to the project itself. E.g. buildtime dependencies for etcd between two released versions (e.g. commit 374a18130a545af9e8d094c7473ab97eff81e71a which is between 2.0.7 and 2.0.8) does not have to list all dependencies: Spec file list only github.com/bmizerany/perks/quantile but Godeps folder contains more:
*   github.com/coreos/etcd/Godeps/_workspace/src/code.google.com/p/goprotobuf/proto
*	github.com/coreos/etcd/Godeps/_workspace/src/code.google.com/p/goprotobuf/proto/testdata
*	github.com/coreos/etcd/Godeps/_workspace/src/github.com/codegangsta/cli
*	github.com/coreos/etcd/Godeps/_workspace/src/github.com/coreos/go-etcd/etcd
*	github.com/coreos/etcd/Godeps/_workspace/src/github.com/gogo/protobuf/proto
*	github.com/coreos/etcd/Godeps/_workspace/src/github.com/golang/protobuf/proto
*	github.com/coreos/etcd/Godeps/_workspace/src/github.com/jonboulle/clockwork
*	github.com/coreos/etcd/Godeps/_workspace/src/github.com/matttproud/golang_protobuf_extensions/ext
*	github.com/coreos/etcd/Godeps/_workspace/src/github.com/prometheus/client_golang/model
*   and more
 
As this dependencies are prefixed with github.com/coreos/etcd they are filtered out (package can not have buildtime dependency on itself). As these import paths are listed in Provides this case can be easily detected.

##### Request review

Once your spec file is prepared another step is to create review request for new package. It means upload the spec file and srpm on public server, run koji build and provide other information, i.e. your FAS name, package description, etc. Running 'gofed review --user=FAS package.spec' in a folder containing spec file does all for you. After succesfull local build and build in koji you get all information printed on stdout. Spec file and srpm are uploaded to your fedorapeople.org webpage. The command requires passwordless ssh connection (you can run ssh-copy-id).

If golang-github-kr-pretty.spec is a spec file you can run:

```vim
$ gofed review golang-github-kr-pretty.spec
```
Output
```vim
Parsing golang-github-kr-pretty.spec file
  Provides: github
  Repo: pretty
  Commit: cb0850c1681cbca3233e84f7e6ec3e4c3f352085
  Name: golang-github-kr-pretty
  Summary: !!!!FILL!!!!

Copying tarball pretty-cb0850c.tar.gz to /home/jchaloup/rpmbuild/SOURCES

Building spec file using rpmbuild
  /home/jchaloup/rpmbuild/SRPMS/golang-github-kr-pretty-0-0.1.gitcb0850c.fc20.src.rpm
  /home/jchaloup/rpmbuild/RPMS/noarch/golang-github-kr-pretty-devel-0-0.1.gitcb0850c.fc20.noarch.rpm

Running rpmlint /home/jchaloup/rpmbuild/SRPMS/golang-github-kr-pretty-0-0.1.gitcb0850c.fc20.src.rpm /home/jchaloup/rpmbuild/RPMS/noarch/golang-github-kr-pretty-devel-0-0.1.gitcb0850c.fc20.noarch.rpm
golang-github-kr-pretty.src: W: invalid-license !!!!FILL!!!!
golang-github-kr-pretty-devel.noarch: W: invalid-license !!!!FILL!!!!
2 packages and 0 specfiles checked; 0 errors, 2 warnings.

Running koji scratch build on srpm
koji build --scratch rawhide /home/jchaloup/rpmbuild/SRPMS/golang-github-kr-pretty-0-0.1.gitcb0850c.fc20.src.rpm --nowait
  Watching rawhide build, http://koji.fedoraproject.org/koji/taskinfo?taskID=9469085
Uploading srpm and spec file to @fedorapeople.org
jchaloup@fedorapeople.org "mkdir -p public_html/reviews/golang-github-kr-pretty"
scp /home/jchaloup/rpmbuild/SRPMS/golang-github-kr-pretty-0-0.1.gitcb0850c.fc20.src.rpm jchaloup@fedorapeople.org:public_html/reviews/golang-github-kr-pretty/.
scp golang-github-kr-pretty.spec jchaloup@fedorapeople.org:public_html/reviews/golang-github-kr-pretty/.


Generating Review Request
###############################################################
Review Request: golang-github-kr-pretty- !!!!FILL!!!!
###############################################################
Spec URL: https://jchaloup.fedorapeople.org/reviews/golang-github-kr-pretty/golang-github-kr-pretty.spec

SRPM URL: https://jchaloup.fedorapeople.org/reviews/golang-github-kr-pretty/golang-github-kr-pretty-0-0.1.gitcb0850c.fc20.src.rpm

Description: !!!!FILL!!!!

Fedora Account System Username: jchaloup

Koji: http://koji.fedoraproject.org/koji/taskinfo?taskID=9469085

$ rpmlint /home/jchaloup/rpmbuild/SRPMS/golang-github-kr-pretty-0-0.1.gitcb0850c.fc20.src.rpm /home/jchaloup/rpmbuild/RPMS/noarch/golang-github-kr-pretty-devel-0-0.1.gitcb0850c.fc20.noarch.rpm
golang-github-kr-pretty.src: W: invalid-license !!!!FILL!!!!
golang-github-kr-pretty-devel.noarch: W: invalid-license !!!!FILL!!!!
2 packages and 0 specfiles checked; 0 errors, 2 warnings.

###############################################################


Enter values at: https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&format=fedora-review

```

##### Building and updating golang packages in Fedora

If your package is updated or if it is a new one there is always a sequence of steps you take in order to get a new build into Koji. For each branch you do:
*   scratch build
*   push
*   build
*   update
*   overrides (optional)

Gofed tool provides a set of commands allowing you to do each of these steps for individual branches at once:
*   gofed scratch-build
*   gofed push
*   gofed build
*   gofed update
*   gofed bbo

Implicitely all branches are taken. Running commands with --branches or --ebranches allows you to specify which branches you run the command on or don't. E.g. 'gofed build --branches="f20,f21"' starts building on f20 and f21 branches. Running 'gofed push --ebranches="f22,master"' pushes all local branches except f20 and f21 to remote repository. To set which branches are updated, overrided or which are taken implicitely can be set at /usr/share/gofed/config/gofed.conf file.

To run all four steps at once (scratch build, push, build, update) you can run 'gofed wizard --scratch'. Or running just push and build you can run 'gofed wizard --push'. For more info run 'gofed wizard --help'.

There are other commands you can use:
*   gofed pull: pull on all branches
*   gofed gcp: git cherry-pick from master branch

#### Scans and inspections of golang source codes

Golang projects can depend on other projects. On the other hand the project itself can be imported in other projects too. To get a list of all imported and provided packages, you can run 'gofed ggi' and 'gofed inspect -p' commands in a source code directory:

```vim
$ cd golang-github-kr-pretty/pretty-cb0850c1681cbca3233e84f7e6ec3e4c3f352085
$ gofed ggi
	github.com/kr/pretty
	github.com/kr/text
$ gofed inspect -p
.
```

Dot means the current directory. As kr/pretty comes from github.com, you can run the command with --prefix option:

```vim
$ gofed inspect -p --prefix="github.com/kr/pretty"
github.com/kr/pretty
```

Running the command on etcd you get:

```vim
$ gofed inspect -p --prefix="github.com/coreos/etcd"
github.com/coreos/etcd/client
github.com/coreos/etcd/discovery
github.com/coreos/etcd/error
github.com/coreos/etcd/etcdctl/command
github.com/coreos/etcd/etcdmain
github.com/coreos/etcd/etcdserver
github.com/coreos/etcd/etcdserver/etcdhttp
...
github.com/coreos/etcd/pkg/coreos
github.com/coreos/etcd/pkg/cors
github.com/coreos/etcd/pkg/crc
github.com/coreos/etcd/pkg/fileutil
github.com/coreos/etcd/pkg/flags
github.com/coreos/etcd/pkg/idutil
...
```

Gofed ggi command with -d option you query PkgDB of a given dependency is already packaged:

```
$ gofed ggi -c -d -v
Class: github.com/kr/pretty (golang-github-kr-pretty) PkgDB=True
Class: github.com/kr/text (golang-github-kr-text) PkgDB=True
```

Some projects provides Godeps.json file containing a list of all imported packages (including commit). This file can be used to check PkgDB for packages which are outdated or new. To run this scan run (-v as verbose display all packages):

```
$ gofed check-deps Godeps.json -v
package golang-googlecode-gogoprotobuf has newer commit
package golang-github-codegangsta-cli has newer commit
package golang-github-coreos-go-etcd has newer commit
package golang-github-jonboulle-clockwork has newer commit
package golang-github-stretchr-testify has newer commit
golang-googlecode-net: upstream commit c5a46024776ec35eb562fa9226968b9d543bb13a not found
```

Running the command without -v option will display only outdated packages and those import paths that are not packaged or their commits was not found (repository was moved, import paths were renamed, etc.).

##### Other use cases

If you find a new use case or there is just one missing, let me know. Good hacking!!!
