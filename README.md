## About

**GolangPackageGenerator** is a set of tools with a goal to automize packaging of golang devel source codes.

What it basically supports:
* github2golang spec file generator
* googlecode2golang spec file generator
* golang imports discovering (dependency on other imports/packages)
* preparation of Review Request for a new golang package
* other usefull commands (parallel push, pull or update of all chosen branches)

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
   $ go2fed github2spec stretchr respond fb9c7353c67cdeccb10af1320b978c5a1e401e9b
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
   
First it clone fedora repo if the package already exists. If not, it creates a spec file (needs to be filled for missing stuff), downloads the tarball and lists all imports.

#### Dependency discovering
To discover imports and dependecies on packages for https://github.com/rackspace/gophercloud, run the following command on its tarball:

   ```vim
   $ go2fed ggi -c -s -d
   ```

Output:

   ```vim
   Class: github.com/mitchellh/mapstructure (golang-github-mitchellh-mapstructure) PkgDB=True
   Class: github.com/racker/perigee (golang-github-racker-perigee) PkgDB=True
   Class: github.com/rackspace/gophercloud (golang-github-rackspace-gophercloud) PkgDB=True
   Class: github.com/tonnerre/golang-pretty (golang-github-tonnerre-golang-pretty) PkgDB=True
   ```

Running with -d option, the go2fed checks if the dependency has a package in PkgDB.
