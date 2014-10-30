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
   https://github.com/stretchr/respond
   Checking if the package already exists in PkgDB
   Cloning into 'golang-github-stretchr-respond'...
   fatal: '/srv/git/rpms//golang-github-stretchr-respond.git' does not appear to be a git repository
   fatal: Could not read from remote repository.

   Please make sure you have the correct access rights
   and the repository exists.
   Could not execute clone: Command '['git', 'clone', 'ssh://jchaloup@pkgs.fedoraproject.org/golang-github-stretchr-respond', '--origin', 'origin']' returned non-zero exit status 128
   Creating spec file
   golang-github-stretchr-respond.spec
   Downloading tarball
   --2014-10-31 00:07:12--  https://github.com/stretchr/respond/archive/fb9c7353c67cdeccb10af1320b978c5a1e401e9b/respond-fb9c735.tar.gz
   Resolving github.com (github.com)... 192.30.252.131
   Connecting to github.com (github.com)|192.30.252.131|:443... connected.
   HTTP request sent, awaiting response... 302 Found
   Location: https://codeload.github.com/stretchr/respond/tar.gz/fb9c7353c67cdeccb10af1320b978c5a1e401e9b [following]
   --2014-10-31 00:07:13--  https://codeload.github.com/stretchr/respond/tar.gz/fb9c7353c67cdeccb10af1320b978c5a1e401e9b
   Resolving codeload.github.com (codeload.github.com)... 192.30.252.147
   Connecting to codeload.github.com (codeload.github.com)|192.30.252.147|:443... connected.
   HTTP request sent, awaiting response... 200 OK
   Length: 4459 (4.4K) [application/x-gzip]
   Saving to: ‘respond-fb9c735.tar.gz’

   100%[===========================================>] 4,459       --.-K/s   in 0.003s  

   2014-10-31 00:07:14 (1.55 MB/s) - ‘respond-fb9c735.tar.gz’ saved [4459/4459]

   Inspecting golang
   	github.com/stretchr/respond
   	github.com/stretchr/testify/require
   /tmp/test/golang-github-stretchr-respond/fedora/golang-github-stretchr-responduildRequires:  golang(github.com/stretchr/testify/assert) 
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
