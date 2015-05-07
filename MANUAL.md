##Manual [DRAFT]

#### Scan of all golang packages for import paths

As there is more than 100 golang devel source code packages
(from here on golang packages), which can depend on other golang packages,
it is easy to break them just by removing or changing one import path.
Due to recent changes of import paths and movement of some repositories,
back-compatibility issue comes to the game.
To keep golang ecosystem in a good shape, automatic scans for broken import
paths and back-compatibility needs to be periodically run.

In order to find which import paths are currently used, there are two cases
we should consider:
* import paths used in non-patched tarballs
* import paths used in patched tarballs

In the first case we get import paths delivered by upstream projects.
In the seconds case we get import paths provided by the ecosystem.
Both of these cases will give us a better picture of what can be provided
and what is provided.

Secondly, import paths can be divided into two types:
* import paths packages use, i.e. imports
* import paths packages provides, i.e. path to all golang files in a given
file hierarchy

One of many problems to deal with is a back-compatibility.
Once from time to time some golang projects change their import path prefix,
some are moved to a different repository. 
To decide if it is possible to change the prefix of import path to a new one,
check through all used import paths is needed.

In order to accomplish this use case, all the latest builds
(patched tarballs case) of all devel packages must be scanned.
In order to speed up querying over found import paths, local database is
created. It can be then queried for example for all import paths
with a given prefix.

You can run:

```vim
    # create local databases of import and imported paths
    $ gofed scan-imports -c
    # list all imported paths starting with code.google.code/p/
    $ gofed scan-imports -i -p code.google.code/p/
    # list only packages that imports paths starting with golang.org/x/
    $ gofed scan-imports -l -p golang.org/x/ -m
```

Other problem is a removal of already provided import paths.
Some projects may decide to move their go files to a different location
or remove them.
To find out if we can do it without breaking already built go binaries
of packaged devel source codes, database can be queried.

#### Golang packages

All golang packages are saved into a local database.
These package usually starts with "golang-" prefix and are easy to find.
You can run the following command to find new packages not yet saved
in the local database:

```vim
   $ gofed scan-packages -n
```

To list all the packages in the database, you can run:

```vim
   $ gofed scan-packages -l
```

Tools like etcd, kubernetes or flannel does not start with the prefix.
These must be added to the database manually.
So it is important to know them otherwise gofed scan-imports does not have to
tell you about used import paths.
If you know about golang packages that does not start with "golang-" prefix
and are not in the database,
send them to jchaloup@redhat.com, subject "Golang new package name". Thanks.

##### Subpackages

Every golang package should consist of one devel subpackage at least.
This package provides source codes which can be imported in other packages
and thus it is good to use "-devel" sufix for its name.
At most cases, every golang package will consists of this package only.
Some projects can be built.
Builds of golang source codes belong to the main package
and should not provide any source codes, only binaries.

To list all possible paths that can be provided, run the following command
in a source code root directory:

```vim
$ gofed inspect -p
```

This command will list all golang packages (possible import paths)
in directory hierarchy.
Some paths can be project specific and be used only for testing.
So the list should be investigated and inessential paths removed.

#### API compatibility

API of each golang project consists of exported symbols.
These can be data types, constants, variables, methods or functions.
In order to provide stable update, API of each update has to be
back-compatible.
Or to some extend at least (does not change symbols that are in use).

##### List of exported symbols

To list exported symbols (divided into types, funcs and vars)
in a current directory you can run:

```vim
$ gofed scan-symbols -l .
```

Output:

```vim
...
Import path: etcdserver
  type: Attributes
  type: Cluster
  type: ClusterInfo
  ...
  func: AddMember
  func: AddMember
  func: ClientURLs
  ...
  var:  DefaultSnapCount
  var:  ErrCanceled
  var:  ErrIDExists
  ...
Import path: raft/raftpb
  ...
```

Type stands for types, func for functions and methods and
var for variables and constants.

##### Comparison of two APIs

To compare two APIs you can run:

```vim
$ gofed apidiff DIR1 DIR2
```

where DIR1, resp. DIR2 stands for directory containing older,
resp. new source codes.
E.g. to compare etcd-2.0.5 and etcd-2.0.7 run:

```vim
$ gofed apidiff etcd-2.0.5 etcd-2.0.7
```

The command implicitly outputs a list of packages (import paths) and all
symbols that has been changed and break back-compatibility.

Output:
```vim
$ gofed apidiff etcd-2.0.5 etcd-2.0.7
    Package: etcdserver
        -VerifyBootstrapConfig func removed
    Package: wal
        -WALv2_0_1 variable/constant removed
        -WALUnknown variable/constant removed
        -WALv0_4 variable/constant removed
        -WALNotExist variable/constant removed
        -WALv2_0Proxy variable/constant removed
        -WALv2_0 variable/constant removed
        -WalVersion type removed
        -DetectVersion func removed
```

Running with --prefix option, all import paths are prefixed:

```vim
    $ gofed apidiff etcd-2.0.5 etcd-2.0.7 --prefix=github.com/coreos
        Package: github.com/coreos/etcdserver
        ...
        Package: github.com/coreos/wal
        ...
```

Apidiff command provides informative output for the moment.
It does not have report all API violations.

#### Missing information

All requests for missing commands, use cases, workflows
or any ideas or suggestions are welcome.
Create a pull request for them. Thanks.
