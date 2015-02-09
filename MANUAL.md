##Manual

#### Scan of all golang packages for import paths

As there is more than 100 golang devel source code packages (from here on golang packages),
which can depend on other golang packages, it is easy to break them just by removing
or changing one import path. Due to recent changes of import paths and movement of some
repositories, back-compatibility issue comes to the game.
To keep golang ecosystem in a good shape, automatic scans for broken import paths and
back-compatibility needs to be periodically.

In order to find which import paths are currently used, there are two cases we should consider:
1. import paths used in non-patched tarballs
2. import paths used in patched tarballs

In the first case, we get import paths delivered by upstream projects.
In the seconds case, we get import paths provided by the ecosystem.
Both of these cases will give us a better picture of what can be provided and what is provided.

Secondly, import paths can be divided into two types:
1. import paths packages use, i.e. imports
2. import paths packages provides, i.e. path to all golang files in a given file hiearchy

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
