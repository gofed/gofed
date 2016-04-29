##Manual [DRAFT]

#### Scan of all golang packages for import paths

As there is more than 100 golang development source code packages
(from here on golang packages), which can depend on other golang packages,
it is easy to break them just by removing or changing one import path.
Due to recent changes of import paths and movement of some repositories,
backward compatibility issue comes to the game.
To keep golang ecosystem in a good shape, automatic scans for broken import
paths and backward compatibility need to be periodically run.

In order to find which import paths are currently used, there are two cases
we should consider:
* import paths used in non-patched tarballs
* import paths used in patched tarballs

In the first case, upstream projects deliver the import paths.
In the seconds case, the ecosystem provides the import paths.
Both of these cases illustrate what is provided and what can be provided.

in addition, import paths can be divided into two types:
* import paths that packages use, that is imports
* import paths that packages provides, that is path to all golang files in a given
file hierarchy

One of many problems to deal with is backward compatibility.
Once from time to time some golang projects change their import path prefix,
some are moved to a different repository. 
To decide if it is possible to change the prefix of import path to a new one,
a check through all used import paths is needed.

In order to accomplish this use case, all the latest builds
(patched tarballs case) of all development packages must be scanned.
In order to speed up querying over found import paths, a local database is
created. It can be then queried for example for all import paths
with a given prefix.

See the following examples:

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
of packaged development source codes, the database can be queried.

#### Golang packages

All golang packages are saved into a local database.
These packages usually start with the "golang-" prefix and are easy to find.
Run the following command to find new packages not yet saved
in the local database:

```vim
   $ gofed scan-packages -n
```

To list all packages in the database, run:

```vim
   $ gofed scan-packages -l
```

Tools like etcd, kubernetes, or flannel does not start with the prefix.
And therefore, they must be added to the database manually.
It is important to be aware of such packages otherwise the "gofed scan-imports" 
command will not list their used import paths.
If you know about golang packages that do not start with the "golang-" prefix
and are not included in the database, send an e-mail with subject "Golang new package name" to 
jchaloup@redhat.com. Thanks.

##### Subpackages

Every golang package should consist at least of one development subpackage.
This package provides source codes which can be imported to other packages,
and thus it is advised to use the "-devel" sufix with the package's name.
In most cases, every golang package consists of this package only.
Some projects can be compiled and provide binaries.
Product of compilation of the golang source codes belong to the main package
and should not provide any source codes, only binaries.

To list all possible paths that can be provided, run the following command
in a source code root directory:

```vim
$ gofed inspect -p
```

This command lists all golang packages (possible import paths)
in a directory hierarchy.
Some paths are project-specific and as such can be used only for testing.
Therefore, the list should be investigated and inessential paths should be removed.

#### API compatibility

API of each golang project consists of exported symbols.
These can be data types, constants, variables, methods, or functions.
In order to provide a stable update, API of each update must be
backward-compatible at least to certain extend (do not change symbols that are in use).

##### List of exported symbols

To list exported symbols (divided into types, funcs, and vars)
in the current directory, run:

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

Type stands for types, func for functions and methods, and
var for variables and constants.

##### Comparison of two APIs

To compare two APIs, run:

```vim
$ gofed apidiff <DIR1> <DIR2>
```

Where <DIR1> and <DIR2> stand for directories containing older and newer source codes, respectively.
For example, to compare etcd-2.0.5 and etcd-2.0.7, run:

```vim
$ gofed apidiff etcd-2.0.5 etcd-2.0.7
```

The command implicitly outputs a list of packages (import paths) and all
symbols that has been changed and that break backward compatibility.

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

When running this command with the --prefix option, all import paths are prefixed:

```vim
    $ gofed apidiff etcd-2.0.5 etcd-2.0.7 --prefix=github.com/coreos
        Package: github.com/coreos/etcdserver
        ...
        Package: github.com/coreos/wal
        ...
```

The "apidiff" command provides only an informative output at this moment.
It does not report all API violations.

#### Missing information

All requests for missing commands, use cases, workflows,
or any ideas or suggestions are welcome.
Create a pull request for them. Thanks.
