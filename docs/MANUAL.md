##Manual [DRAFT]

#### Scan of all golang packages for import paths

As there is more than 200 golang project packaged in Fedora distribution
(from here on golang packages), which can depend on other golang packages,
it is easy to break them just by removing or changing one imported path.
Due to recent changes of import paths and movement of some repositories,
backward compatibility issue comes to play.
To keep golang ecosystem in a good shape, automatic scans for broken import
paths and backward compatibility need to be run periodically.

In order to find which import paths are currently used, there are two cases
we should consider:
* import paths used in non-patched tarballs
* import paths used in patched tarballs

In the first case, upstream projects deliver the import paths.
In the seconds case, the ecosystem provides the import paths.
Both of these cases illustrate what is provided and what can be provided.

In addition, import paths can be divided into two types:
* import paths that packages use (all imported Go package)
* import paths that packages provides (path to all golang package in project's file hierarchy)

Backward compatibility is one of many problems to deal with.
From time to time some golang projects change their import path prefix,
some are moved to a different repository. 
To decide if it is possible to change the prefix of import path to a new one,
scan through all imported paths is needed.

Other problem is a removal of already provided import paths.
Some projects may decide to move their go files to a different location
or remove them.

In order to accomplish various use cases, all the latest builds
(patched tarballs case) of all golang packages must be scanned periodically.

To scan the latest golang packages, you can run:

```sh
$ gofed scan-distro -v
```

The scan retrieves a list of the latest builds in Fedora's ``rawhide``,
for each build retrieves a list of all relevant rpms (carrying source code)
and from each rpm extracts data such as:

* list of exported symbols (API)
* list of dependencies
* list of defined packages
* list of main packages and unit-test directories

Data extracted by ``gofed scan-distro -v`` are then used by other commands, e.g.

* **gofed scan-deps** constructing dependency graph and detecting defined/missing import paths
* **gofed check-deps** checking project's snapshot (e.g. is project's dependency up-to-date or outdated)
* **gofed scan-packages** retriving a list of builds for golang packages

and other commands.

The command is also responsible for retrieving a list of golang packages.
All packages prefixed with ``golang-`` are included in the list.
For packages that does not start with the prefix can be manually included
using ``--custom-packages="PACKAGE,PACKAGE,..."`` option.
To exclude package, ``--blacklust="PACKAGE,PACKAGE,..."`` option can be used.

For example, running ``gofed scan-distro -v --custom-packages="kubernetes,etcd" will
scan latest builds of all packages prefixed with ``golang-`` together with ``kubernetes``
and ``etcd``.

Among other data, the ``gofed scan-distro`` command produces a distribution snapshot
keeping all builds currently scanned.

If you know about golang packages that do not start with the "golang-" prefix
and are not included in any distribution snapshot,
you can send an e-mail with subject "Golang new package name" to 
jchaloup@redhat.com. Thanks.

##### Subpackages

Every golang package should consist of one development subpackage at least.
This package provides source codes which can be imported by other packages,
and thus it is advised to use the "-devel" sufix within the package's name.
In most cases, every golang package consists of this package only.
Some projects can be compiled and provide binaries.
Product of compilation of the golang source codes belong to the main package
and should not provide any source code, only binaries.

To list all possible paths that can be provided, run the following command
in project's root directory:

```vim
$ gofed inspect -p
```

The command lists all golang packages (possible import paths)
in project's directory hierarchy.
Some paths are project-specific and as such can be used only for testing.
Therefore, ithe list should be investigated and inessential paths removed.

#### API compatibility

API of each golang project consists of exported symbols.
These can be data types, constants, variables, methods, or functions.
In order to provide a stable update, API of each update must be
backward-compatible at least to certain extend (do not change symbols that are in use).

##### Comparison of two APIs

To compare two APIs, run:

   ```vim
   $ gofed apidiff --reference="upstream:project[:commit]" --compare-with="upstream:project[:commit]"
   ```
For example, to check API of etcd between etcd-2.3.3 and etcd-2.2.4, run:

   ```vim
   $ gofed apidiff --reference="upstream:github.com/coreos/etcd:c41345d393002e87ae9e7023234b1c1e04ba9626" --compare-with="upstream:github.com/coreos/etcd:bdee27b19e8601ffd7bd4f0481abe9bbae04bd09"
   ```
Commit ``c41345d393002e87ae9e7023234b1c1e04ba9626`` correponds to ``etcd-v2.3.3``, commit ``bdee27b19e8601ffd7bd4f0481abe9bbae04bd09`` to ``etcd-v2.2.4``.

   
   Output
   
   ```vim
   -etcdctlv3/command: function removed: NewDeleteRangeCommand
   -etcdctlv3/command: function removed: NewRangeCommand
   -etcdserver/api/v3rpc: function removed: New
   -etcdserver/api/v3rpc: function removed: handler.Compact
   -etcdserver/api/v3rpc: function removed: handler.DeleteRange
   -etcdserver/api/v3rpc: function removed: handler.Put
   -etcdserver/api/v3rpc: function removed: handler.Range
   -etcdserver/api/v3rpc: function removed: handler.Txn
   ...
   ```
   
   To get new symbols and other information, use the -a option:
   
   ```vim
   ...
   +etcdctlv3/command: new function: NewGetCommand
   +etcdctlv3/command: new function: simplePrinter.Get
   +etcdctlv3/command: new function: NewCompactionCommand
   +etcdctlv3/command: new function: simplePrinter.Watch
   ~etcdctlv3/command: function updated: -type differs: selector != pointer
   ~etcdctlv3/command: function updated: -type differs: selector != pointer
   -etcdctlv3/command: function removed: NewDeleteRangeCommand
   -etcdctlv3/command: function removed: NewRangeCommand
   +etcdctlv3/command: new variable: ExitIO
   +etcdctlv3/command: new variable: ExitInvalidInput
   +etcdctlv3/command: new variable: ExitBadArgs
   +etcdctlv3/command: new variable: ExitError
   +etcdctlv3/command: new variable: ExitBadConnection
   ...
   ```
   
Lines starting with the minus symbol ("-") are breaking backward compatibility.
Lines starting with the plus symbol ("+") are new.
Lines starting with the tilda symbol ("~") are updated.

When running this command with the --prefix option, all import paths are prefixed:
   ```vim
   $ gofed apidiff --reference="upstream:github.com/coreos/etcd:c41345d393002e87ae9e7023234b1c1e04ba9626" --compare-with="upstream:github.com/coreos/etcd:bdee27b19e8601ffd7bd4f0481abe9bbae04bd09" --prefix github.com/coreos/etcd
   ...
   +github.com/coreos/etcd/etcdctlv3/command: new function: NewCompactionCommand
   +github.com/coreos/etcd/etcdctlv3/command: new function: simplePrinter.Watch
   ~github.com/coreos/etcd/etcdctlv3/command: function updated: -type differs: selector != pointer
   ~github.com/coreos/etcd/etcdctlv3/command: function updated: -type differs: selector != pointer
   -github.com/coreos/etcd/etcdctlv3/command: function removed: NewDeleteRangeCommand
   ...
   ```

The ``gofed apidiff`` command provides only an informative output at this moment.
It does not report all API violations.

#### Missing information

All requests for missing commands, use cases, workflows,
or any ideas or suggestions are welcome.
Plese, create a pull request or open an issue for them. Thanks.
