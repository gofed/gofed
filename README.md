## About

**GolangPackageGenerator** is a set of tools with a goal to automate packaging of golang devel source codes.

What it basically supports:
* spec file generator for github.com, code.google.com and bitbucket.org repositories
* preparation of Fedora's Review Request for a new golang package
* golang imports discovering (dependency on other imports/packages)
* comparsion of APIs (exported symbols) of two golang projects
* scan of available golang packages, construction of dependency graphs of packages
* other usefull commands (parallel push, pull or update of all chosen branches, ...)

## Instalation
The repo provides a spec file for Fedora. The package can be build as:

   ```vim
   $ wget https://github.com/ingvagabund/GolangPackageGenerator/archive/<commit>/gpg-<shortcommit>.tar.gz
   $ cp gpg-<shortcommit>.tar.gz /home/<user>/rpmbuild/SOURCES/.
   $ rpmbuild -ba *.spec
   $ rpm -Uvh <built rpm>.rpm
   ```

## Launch it
To generate spec file for github repository https://github.com/stretchr/respond:

   ```vim
   $ gofed github2spec stretchr respond fb9c7353c67cdeccb10af1320b978c5a1e401e9b
   ```

Output:
   ```vim
   Repo URL:
   https://github.com/stretchr/respond

   (1/4) Checking if the package already exists in PkgDB
   (2/4) Creating spec file
   (3/4) Downloading tarball
   (4/4) Discovering golang dependencies
   Class: github.com/stretchr/testify (golang-github-stretchr-testify) PkgDB=True

   Spec file golang-github-stretchr-respond.spec at:
   /tmp/test/golang-github-stretchr-respond/fedora/golang-github-stretchr-respond
   ```
   
First it checks fedora repo if the package already exists. If not, it creates a spec file (needs to be filled for missing data), downloads the tarball and lists all dependencies (classes of imports decomposed by a repository (common import path prefix).

#### Dependency discovering
To discover imports and dependecies on packages for https://github.com/rackspace/gophercloud, run the following command on its tarball:

   ```vim
   $ gofed ggi -c -s -d
   ```

Output:

   ```vim
   Class: github.com/mitchellh/mapstructure (golang-github-mitchellh-mapstructure) PkgDB=True
   Class: github.com/racker/perigee (golang-github-racker-perigee) PkgDB=True
   Class: github.com/rackspace/gophercloud (golang-github-rackspace-gophercloud) PkgDB=True
   Class: github.com/tonnerre/golang-pretty (golang-github-tonnerre-golang-pretty) PkgDB=True
   ```

Running with -d option, the gofed checks if the dependency is already packaged in PkgDB.

#### Check of up2date dependencides in Fedora
To check if all dependecies are at least up2date in Fedora (e.g. kubernetes), run the following command on its Godeps.json file:

   ```vim
   $ gofed check-deps Godeps.json
   ```

Output:

   ```vim
   package golang-github-davecgh-go-spew outdated
   package golang-github-onsi-gomega outdated
   package golang-github-onsi-ginkgo outdated
   package golang-github-ghodss-yaml outdated
   package golang-github-spf13-pflag outdated
   ```

Running with -v option display status of all dependencies.
Running with -l option will not run git|hg pull on each repository.

