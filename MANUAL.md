##Manual [DRAFT]

#### Scan of all golang packages for import paths

As there is more than 100 golang devel source code packages (from here on golang packages),
which can depend on other golang packages, it is easy to break them just by removing
or changing one import path. Due to recent changes of import paths and movement of some
repositories, back-compatibility issue comes to the game.
To keep golang ecosystem in a good shape, automatic scans for broken import paths and
back-compatibility needs to be periodically run.

In order to find which import paths are currently used, there are two cases we should consider:
* import paths used in non-patched tarballs
* import paths used in patched tarballs

In the first case we get import paths delivered by upstream projects.
In the seconds case we get import paths provided by the ecosystem.
Both of these cases will give us a better picture of what can be provided and what is provided.

Secondly, import paths can be divided into two types:
* import paths packages use, i.e. imports
* import paths packages provides, i.e. path to all golang files in a given file hiearchy

One of many problems to deal with is a back-compatibility.
Once from time to time some golang projects change their import path prefix,
some are moved to a different repository. 
To decide if it is possible to change the prefix of import path to a new one,
check through all used import paths is needed.

In order to accomplish this use case, all the latest builds (patched tarballs case) of all devel packages must be scanned.
In order to speed up querying over found import paths, local database is created. It can be then queried for example for all import paths with a given prefix.

You can run:

```vim
    $ go2fed scan-imports -c    # create local databases of import and imported paths
    $ go2fed scan-imports -i -p code.google.code/p/     # list all imported paths starting with code.google.code/p/
    $ go2fed scan-imports -l -p golang.org/x/ -m        # list only packages that imports paths starting with golang.org/x/
```

Other problem is a removal of already provided import paths.
Some projects may decide to move their go files to a different location or remove them.
To find out if we can do it without breaking already built go binaries of packaged devel source codes,
database can be quieried.

#### Golang packages

All golang packages are saved into a local database. These package usually starts with "golang-" prefix and are easy to find.
You can run the following command to find new packages not yet saved in the local database:

```vim
   $ go2fed scan-packages -n
```

To list all the packages in the database, you can run:

```vim
   $ go2fed scan-packages -l
```

Tools like etcd, kubernetes or flannel does not start with the prefix.
These must be added to the database manually.
So it is important to know them otherwise go2fed scan-imports does not have to tell you about used import paths.
If you know about golang packages that does not start with "golang-" prefix and are not in the database,
send them to jchaloup@redhat.com, subject "Golang new package name". Thanks.

##### Subpackages

Every golang package should consist of one devel subpackage at least.
This package provides source codes which can be imported in other packages and thus it is good to used "-devel" sufix for its name.
At most cases, every golang package will consists of this package only.
Some projects can be built.
Builds of golang source codes belongs to the main package
and should not provide any source codes, only binaries.

To list all possible paths that can be provided, run the following command in a source code root directory:

```vim
$ go2fed inspect -p
```

This command will list paths to all directories containing at least one golang file (*.go).
Some paths can be project specific and be used only for testing.
So the list should be investigated and inessential paths removed.
