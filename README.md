GolangPackageGenerator
======================

Generates Fedora spec file for golang package

Example:
./github2gospec.sh tools godep 754ee6f4e0e5fc8d0ef2692fb239d15c7a09dd84

./github2gospec.sh project repo commit

First it clone fedora repo if the package already exists. If not, it creates a spec file (needs to be filled for missing stuff), downloads the tarball and lists all imports (some are false = contained in comments).
