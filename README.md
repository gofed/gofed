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
   
First it checks fedora repo if the package already exists. If not, it creates a spec file (needs to be filled for missing stuff), downloads the tarball and lists all dependencies (classes of imports decomposed by a repo).

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

#### Scan of golang builds
There is a lot of golang packages in Fedora.
Every build can bring new import paths, some may be obsoleted.
This command allows to check missing or obsoleted provides, find executables and other information.
This tool is still under development, these are only basic tests.

Packages to scan are listed in golang.packages file.
To run the scan, use:

   ```vim
   $ go2fed scan
   ```

Output:

   ```vim
   Scanning golang-bitbucket-kardianos-osext...
   golang-bitbucket-kardianos-osext el6 (0), f21 (0), f20 (0), master (0)
   Scanning golang-github-abbot-go-http-auth...
   golang-github-abbot-go-http-auth el6 (0), f21 (0), f20 (0), master (0)
   Scanning golang-github-bmizerany-assert...
   golang-github-bmizerany-assert el6 (1), f21 (1), f20 (0), master (1)
   Scanning golang-github-bmizerany-pat...
   golang-github-bmizerany-pat el6 (2), f21 (2), f20 (0), master (2)
   Scanning golang-github-BurntSushi-toml...
   golang-github-BurntSushi-toml el6 (0), f21 (0), f20 (0), master (0)
   Scanning golang-github-codegangsta-cli...
   golang-github-codegangsta-cli el6 (0), f21 (0), f20 (0), master (0)
   Scanning golang-github-coreos-go-etcd...
   golang-github-coreos-go-etcd el6 (0), f21 (1), f20 (0), master (1)
   ...
   ```
Result of scans are a set of xml files saved into the current folder.

To display summary of all results, run the following command in the folder:

   ```vim
   $ go2fed scaninfo *.xml
   ```

Output

   ```vim
   golang-bitbucket-kardianos-osext         el6 (0), f21 (0), f20 (0), master (0)
   golang-github-abbot-go-http-auth         el6 (0), f21 (0), f20 (0), master (0)
   golang-github-bmizerany-assert           el6 (1), f21 (1), f20 (0), master (1)
   golang-github-bmizerany-pat              el6 (2), f21 (2), f20 (0), master (2)
   golang-github-BurntSushi-toml            el6 (6), f21 (6), f20 (0), master (6)
   golang-github-codegangsta-cli            el6 (0), f21 (0), f20 (0), master (0)
   golang-github-coreos-go-etcd             el6 (0), f21 (1), f20 (0), master (1)
   golang-github-coreos-go-log              el6 (0), f21 (0), f20 (0), master (0)
   golang-github-coreos-go-semver           f21 (0), master (1)
   golang-github-coreos-go-systemd          el6 (4), f21 (6), f20 (6), master (4)
   ```

If the scaninfo warns you about missing provides which are not missing (or other scanned properties),
user can set those provides in golang.implicit.
Scaninfo then skip these warnings.

To display more information about individual package, run the command with -d option:

   ```vim
   $ go2fed scaninfo golang-github-coreos-go-systemd.xml -d
   ```

Output

   ```vim
   ==========branch: master==========
   build: golang-github-coreos-go-systemd-devel-2-2.fc22.noarch.rpm
   Incorrect provides:
        github.com/coreos/go-systemd
   Missing provides:
        github.com/coreos/go-systemd/login1
        github.com/coreos/go-systemd/examples/activation
        github.com/coreos/go-systemd/examples/activation/httpserver

   ==========branch: f21==========
   build: golang-github-coreos-go-systemd-devel-2-1.fc21.noarch.rpm
   Incorrect provides:
        github.com/coreos/go-systemd
   Missing provides:
        github.com/coreos/go-systemd/unit
        github.com/coreos/go-systemd/examples/activation/httpserver
        github.com/coreos/go-systemd/daemon
        github.com/coreos/go-systemd/examples/activation
        github.com/coreos/go-systemd/login1

   ==========branch: f20==========
   build: golang-github-coreos-go-systemd-devel-0-0.3.git68bc612.fc20.noarch.rpm
   Incorrect provides:
        github.com/coreos/go-systemd
   Missing provides:
        github.com/coreos/go-systemd/unit
        github.com/coreos/go-systemd/examples/activation/httpserver
        github.com/coreos/go-systemd/daemon
        github.com/coreos/go-systemd/examples/activation
        github.com/coreos/go-systemd/login1

   ==========branch: el6==========
   build: golang-github-coreos-go-systemd-devel-2-2.el6.i686.rpm
   Incorrect provides:
        github.com/coreos/go-systemd
   Missing provides:
        github.com/coreos/go-systemd/login1
        github.com/coreos/go-systemd/examples/activation
        github.com/coreos/go-systemd/examples/activation/httpserver
   ```
#### Check of up2date dependencides in Fedora
To check if all dependecies are at least up2date in Fedora (e.g. kubernetes), run the following command on its Godeps.json file:

   ```vim
   $ go2fed check-deps Godeps.json
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

