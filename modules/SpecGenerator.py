from ProviderPrefixes import ProviderPrefixes
import os
import sys

from gofed_lib.importpathparserbuilder import ImportPathParserBuilder
from gofed_lib.repositoryinfo import RepositoryInfo
from gofed_lib.importpathparser import GITHUB, GOOGLECODE, BITBUCKET

class SpecGenerator:

	def __init__(self, with_build = False, with_extra = False):
		self.with_build = with_build
		self.with_extra = with_extra

		self.file = sys.stdout

	def generateHeaderEpilogue(self):
		self.file.write("%if 0%{?fedora} || 0%{?rhel} == 6\n")
		self.file.write("%global with_devel 1\n")
		self.file.write("%global with_bundled 0\n")

		# if generated with build section generate debuginfo as well
		if self.with_build:
			self.file.write("%global with_debug 1\n")
		else:
			self.file.write("%global with_debug 0\n")

		self.file.write("%global with_check 1\n")
		self.file.write("%global with_unit_test 1\n")
		self.file.write("%else\n")
		self.file.write("%global with_devel 0\n")
		self.file.write("%global with_bundled 0\n")
		self.file.write("%global with_debug 0\n")
		self.file.write("%global with_check 0\n")
		self.file.write("%global with_unit_test 0\n")
		self.file.write("%endif\n\n")

		# debug
		self.file.write("%if 0%{?with_debug}\n")
		self.file.write("%global _dwz_low_mem_die_limit 0\n")
		self.file.write("%else\n")
		self.file.write("%global debug_package   %{nil}\n")
		self.file.write("%endif\n\n")

		# %gobuild macro default definition
		if self.with_extra and self.with_build:
			self.file.write("%if ! 0%{?gobuild:1}\n")
			self.file.write("%define gobuild(o:) go build -ldflags \"${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\\\n')\" -a -v -x %{?**};\n")
			self.file.write("%endif\n")
			self.file.write("\n")

	def generateGithubHeader(self, project, repository, url, provider_prefix, commit, licenses):
		self.file.write("%global provider        github\n")
		self.file.write("%global provider_tld    com\n")
		self.file.write("%%global project         %s\n" % project)
		self.file.write("%%global repo            %s\n" % repository)
		self.file.write("# https://%s\n" % provider_prefix)
		self.file.write("%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}\n")

		if url != provider_prefix:
			self.file.write("%%global import_path     %s\n" % url)
		else:
			self.file.write("%global import_path     %{provider_prefix}\n")

                self.file.write("%%global commit          %s\n" % commit)
		self.file.write("%global shortcommit     %(c=%{commit}; echo ${c:0:7})\n\n")
		self.file.write("Name:           golang-%{provider}-%{project}-%{repo}\n")
		self.file.write("Version:        0\n")
		self.file.write("Release:        0.0.git%{shortcommit}%{?dist}\n")
		self.file.write("Summary:        !!!!FILL!!!!\n")
		if licenses != []:
			self.file.write("# Detected licences\n")
		for license in licenses:
			self.file.write("# - %s at '%s'\n" % (license["type"], license["file"]))
		self.file.write("License:        !!!!FILL!!!!\n")
		self.file.write("URL:            https://%{provider_prefix}\n")
		self.file.write("Source0:        https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz\n")

	def generateGooglecodeHeader(self, repository, url, provider_prefix, commit, licenses):
		parts = repository.split(".")
		stripped_repo = parts[-1]
		rrepository = ".".join(parts[::-1])
		self.file.write("%global provider        google\n")
		self.file.write("%global provider_sub    code\n")
		self.file.write("%global provider_tld    com\n")
		self.file.write("%global project         p\n")
		self.file.write("%%global repo            %s\n" % repository)
		self.file.write("%%global rrepo           %s\n" % rrepository)
		self.file.write("# https://%s\n" % provider_prefix)
		self.file.write("%global provider_prefix %{provider_sub}.%{provider}.%{provider_tld}/%{project}/%{repo}\n")

		if url != provider_prefix:
			self.file.write("%%global import_path     %s\n" % url)
		else:
			self.file.write("%global import_path     %{provider_prefix}\n")

		self.file.write("%%global rev             %s\n" % commit)
		self.file.write("%global shortrev        %(c=%{rev}; echo ${c:0:12})\n\n")
		self.file.write("Name:           golang-%%{provider}%%{provider_sub}-%s\n" % stripped_repo)
		self.file.write("Version:        0\n")
		self.file.write("Release:        0.0.hg%{shortrev}%{?dist}\n")
		self.file.write("Summary:        !!!!FILL!!!!\n")
		if licenses != []:
			self.file.write("# Detected licences\n")
		for license in licenses:
			self.file.write("# - %s at '%s'\n" % (license["type"], license["file"]))
		self.file.write("License:        !!!!FILL!!!!\n")
		self.file.write("URL:            https://%{provider_prefix}\n")
		self.file.write("Source0:        https://%{rrepo}.%{provider}%{provider_sub}.%{provider_tld}/archive/%{rev}.tar.gz\n")

	def generateBitbucketHeader(self, project, repository, url, provider_prefix, commit, licenses):
		self.file.write("%global provider        bitbucket\n")
		self.file.write("%global provider_tld    org\n")
		self.file.write("%%global project         %s\n" % project)
		self.file.write("%%global repo            %s\n" % repository)
		self.file.write("# https://%s\n" % provider_prefix)
		self.file.write("%%global provider_prefix %s\n" % provider_prefix)
		self.file.write("%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}\n")

		if url != provider_prefix:
			self.file.write("%%global import_path     %s\n" % url)
		else:
			self.file.write("%global import_path     %{provider_prefix}\n")

		self.file.write("%%global commit          %s\n" % commit)
		self.file.write("%global shortcommit     %(c=%{commit}; echo ${c:0:12})\n\n")
		self.file.write("Name:           golang-%{provider}-%{project}-%{repo}\n")
		self.file.write("Version:        0\n")
		self.file.write("Release:        0.0.git%{shortcommit}%{?dist}\n")
		self.file.write("Summary:        !!!!FILL!!!!\n")
		self.file.write("License:        !!!!FILL!!!!\n")
		if licenses != []:
			self.file.write("# Detected licences\n")
		for license in licenses:
			self.file.write("# - %s at '%s'\n" % (license["type"], license["file"]))
		self.file.write("URL:            https://%{provider_prefix}\n")
		self.file.write("Source0:        https://%{provider_prefix}/get/%%{shortcommit}.tar.gz\n")

	def generateHeaderPrologue(self, main_packages, prefix):
		self.file.write("# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required\n")
		self.file.write("ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 %{arm}}\n")
		# Once BuildRequires of the compiler is removed from the main package, put it back to unit-test-devel subpackage.
		# Otherwise %check section can not run 'go test' on tests package in the unit-test-devel subpackage.
		self.file.write("# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.\n")
		self.file.write("BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}\n\n")

		if self.with_build:
			self.file.write("%if ! 0%{?with_bundled}\n")
			for package in main_packages:
				deps = filter(lambda l: not l.startswith(prefix), package["dependencies"])

				if deps == []:
					continue

				self.file.write("# %s\n" % package["path"])
				for dep in deps:
					self.file.write("BuildRequires: golang(%s)\n" % (dep))

				self.file.write("\n")

			# generate dependency on devel too
			self.file.write("# binaries are built from devel subpackage\n")
			self.file.write("BuildRequires: %{name}-devel = %{version}-%{release}\n")

			self.file.write("%endif\n\n")

                self.file.write("%description\n")
                self.file.write("%{summary}\n")
                self.file.write("\n")

	def generateDevelHeader(self, devel_packages, prefix):
		self.file.write("%if 0%{?with_devel}\n")
                self.file.write("%package devel\n")
                self.file.write("Summary:       %{summary}\n")
                self.file.write("BuildArch:     noarch\n")
                self.file.write("\n")

		# dependencies
		imported_packages = []
		for package in devel_packages:
			imported_packages.extend(package["dependencies"])

		imported_packages = filter(lambda l: not l.startswith(prefix), imported_packages)
		imported_packages = sorted(list(set(imported_packages)))

		self.file.write("%if 0%{?with_check} && ! 0%{?with_bundled}\n")
		for dep in imported_packages:
			self.file.write("BuildRequires: golang(%s)\n" % (dep))
		self.file.write("%endif\n")

		if imported_packages != []:
			self.file.write("\n")
			for dep in imported_packages:
				self.file.write("Requires:      golang(%s)\n" % (dep))

		# provides
		self.file.write("\n")
		for path in sorted(map(lambda l: l["package"], devel_packages)):
			# skip all provided packages with /internal/ keyword
			if "internal" in path.split("/"):
				continue

			sufix = ""
			if path != ".":
				sufix = "/%s" % path

			self.file.write("Provides:      golang(%%{import_path}%s) = %%{version}-%%{release}\n" % sufix)

		# description
		self.file.write("\n%description devel\n")
		self.file.write("%{summary}\n\n")
		self.file.write("This package contains library source intended for\n")
		self.file.write("building other packages which use import path with\n")
		self.file.write("%{import_path} prefix.\n")
		self.file.write("%endif\n")

	def generateUnitTestHeader(self, tests, devel_packages, prefix):
		self.file.write("%if 0%{?with_unit_test} && 0%{?with_devel}\n")
		self.file.write("%package unit-test-devel\n")
		self.file.write("Summary:         Unit tests for %{name} package\n")
		self.file.write("%if 0%{?with_check}\n")
		self.file.write("#Here comes all BuildRequires: PACKAGE the unit tests\n#in %%check section need for running\n")
		self.file.write("%endif\n")
		self.file.write("\n")
		self.file.write("# test subpackage tests code from devel subpackage\n")
		self.file.write("Requires:        %{name}-devel = %{version}-%{release}\n")
		self.file.write("\n")

		# dependencies
		imported_packages = []
		for package in devel_packages:
			imported_packages.extend(package["dependencies"])

		imported_packages = filter(lambda l: not l.startswith(prefix), imported_packages)
		imported_packages = sorted(imported_packages)

		test_imported_packages = []
		for test in tests:
			test_imported_packages.extend(test["dependencies"])

		test_deps = sorted(list(set(test_imported_packages) - set(imported_packages)))
		test_deps = filter(lambda l: not l.startswith(prefix), test_deps)

		self.file.write("%if 0%{?with_check} && ! 0%{?with_bundled}\n")
		for dep in test_deps:
			self.file.write("BuildRequires: golang(%s)\n" % (dep))
		self.file.write("%endif\n")

		if test_deps != []:
			self.file.write("\n")
			for dep in test_deps:
				self.file.write("Requires:      golang(%s)\n" % (dep))
		self.file.write("\n")

		self.file.write("%description unit-test-devel\n")
		self.file.write("%{summary}\n")
		self.file.write("\n")
		self.file.write("This package contains unit tests for project\nproviding packages with %{import_path} prefix.\n")
		self.file.write("%endif\n")

	def generatePrepSection(self, provider):
		self.file.write("%prep\n")

		if provider == GOOGLECODE:
			self.file.write("%setup -q -n %{rrepo}-%{shortrev}\n")
		elif provider == BITBUCKET:
			self.file.write("%setup -q -n %{project}-%{repo}-%{shortcommit}\n")
		else:
			self.file.write("%setup -q -n %{repo}-%{commit}\n")

	def generateBuildSection(self, url, main_packages):
		self.file.write("%build\n")

		if self.with_build:
			parts = url.split("/")

			# building itself
			self.file.write("mkdir -p src/%s\n" % "/".join(parts[:-1]))
			self.file.write("ln -s ../../../ src/%s\n" % url)
			self.file.write("\n")
			self.file.write("%if ! 0%{?with_bundled}\n")
			self.file.write("export GOPATH=$(pwd):%{gopath}\n")
			self.file.write("%else\n")
			self.file.write("export GOPATH=$(pwd):$(pwd)/Godeps/_workspace:%{gopath}\n")
			self.file.write("%endif\n")
			self.file.write("\n")

			main_names = sorted(list(set(map(lambda l: os.path.dirname(l["path"]), main_packages))))
			for name in main_names:
				self.file.write("#%%gobuild -o bin/%s %%{import_path}/%s\n" % (name, name))

	def generateInstallSection(self, main_packages, dependency_directories):
		deps_vgrep = ""
		if dependency_directories != []:
			deps_vgrep = "egrep -v \"%s\"" % "|".join(map(lambda l: "./%s" % l, dependency_directories))

		self.file.write("%install\n")
		if self.with_build:
			self.file.write("install -d -p %{buildroot}%{_bindir}\n")

			main_names = sorted(list(set(map(lambda l: os.path.dirname(l["path"]), main_packages))))
			for name in main_names:
				self.file.write("#install -p -m 0755 bin/%s %%{buildroot}%%{_bindir}\n" % name)

			self.file.write("\n")

		self.file.write("# source codes for building projects\n")
		self.file.write("%if 0%{?with_devel}\n")
		self.file.write("install -d -p %{buildroot}/%{gopath}/src/%{import_path}/\n")
		self.file.write("echo \"%%dir %%{gopath}/src/%%{import_path}/.\" >> devel.file-list\n")
		self.file.write("# find all *.go but no *_test.go files and generate devel.file-list\n")
		if deps_vgrep != "":
			self.file.write("for file in $(find . -iname \"*.go\" \! -iname \"*_test.go\" | %s) ; do\n" % deps_vgrep)
		else:
			self.file.write("for file in $(find . -iname \"*.go\" \! -iname \"*_test.go\") ; do\n")
		self.file.write("    echo \"%%dir %%{gopath}/src/%%{import_path}/$(dirname $file)\" >> devel.file-list\n")
		self.file.write("    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)\n")
		self.file.write("    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file\n")
		self.file.write("    echo \"%%{gopath}/src/%%{import_path}/$file\" >> devel.file-list\n")
		self.file.write("done\n")
		self.file.write("%endif\n\n")

		self.file.write("# testing files for this project\n")
		self.file.write("%if 0%{?with_unit_test} && 0%{?with_devel}\n")
		self.file.write("install -d -p %{buildroot}/%{gopath}/src/%{import_path}/\n")
		self.file.write("# find all *_test.go files and generate unit-test-devel.file-list\n")
		if deps_vgrep != "":
			self.file.write("for file in $(find . -iname \"*_test.go\" | %s) ; do\n" % deps_vgrep)
		else:
			self.file.write("for file in $(find . -iname \"*_test.go\"); do\n")
		self.file.write("    echo \"%%dir %%{gopath}/src/%%{import_path}/$(dirname $file)\" >> devel.file-list\n")
		self.file.write("    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)\n")
		self.file.write("    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file\n")
		self.file.write("    echo \"%%{gopath}/src/%%{import_path}/$file\" >> unit-test-devel.file-list\n")
		self.file.write("done\n")
		self.file.write("%endif\n\n")

		self.file.write("%if 0%{?with_devel}\n")
		self.file.write("sort -u -o devel.file-list devel.file-list\n")
		self.file.write("%endif\n")

	def generateCheckSection(self, test_directories):
		self.file.write("%check\n")
		self.file.write("%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}\n")
		self.file.write("%if ! 0%{?with_bundled}\n")
		self.file.write("export GOPATH=%{buildroot}/%{gopath}:%{gopath}\n")
		self.file.write("%else\n")
		self.file.write("export GOPATH=%{buildroot}/%{gopath}:$(pwd)/Godeps/_workspace:%{gopath}\n")
		self.file.write("%endif\n\n")

		# %gotest macro default definition
		if self.with_extra:
			self.file.write("%if ! 0%{?gotest:1}\n")
			self.file.write("%global gotest go test\n")
			self.file.write("%endif\n\n")

		sdirs = sorted(map(lambda l: l["test"], test_directories))
                for dir in sdirs:

			sufix = ""
			if dir != ".":
				sufix = "/%s" % dir

			self.file.write("%%gotest %%{import_path}%s\n" % sufix)
		self.file.write("%endif\n")

	def generateFilesSection(self, provider, docs, licenses, main_packages, ip_prefix = ""):
		self.file.write("#define license tag if not already defined\n")
		self.file.write("%{!?_licensedir:%global license %doc}\n\n")

		if self.with_build:
			self.file.write("%files\n")
			if licenses != "":
				self.file.write("%%license %s\n" % (" ".join(map(lambda l: l["file"], licenses))))
			if docs != []:
				self.file.write("%%doc %s\n" % (" ".join(docs)))


			main_names = sorted(list(set(map(lambda l: os.path.dirname(l["path"]), main_packages))))
			for name in main_names:
				self.file.write("#%%{_bindir}/%s\n" % name)

			self.file.write("\n")

		self.file.write("%if 0%{?with_devel}\n")
		self.file.write("%files devel -f devel.file-list\n")

		if licenses != "":
			self.file.write("%%license %s\n" % (" ".join(map(lambda l: l["file"], licenses))))
		if docs != []:
			self.file.write("%%doc %s\n" % (" ".join(docs)))

		# http://www.rpm.org/max-rpm/s1-rpm-inside-files-list-directives.html
		# it takes every dir and file recursively
		if provider in [GITHUB, BITBUCKET]:
			if ip_prefix != "":
				pp_obj = ProviderPrefixes()
				ok, prefixes = pp_obj.loadCommonProviderPrefixes()
				if not ok or ip_prefix not in prefixes:
					self.file.write("%%dir %%{gopath}/src/%s\n" % ip_prefix)
			else:
				self.file.write("%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}\n")

		self.file.write("%endif\n\n")

		self.file.write("%if 0%{?with_unit_test} && 0%{?with_devel}\n")
		self.file.write("%files unit-test-devel -f unit-test-devel.file-list\n")

		if licenses != "":
			self.file.write("%%license %s\n" % (" ".join(map(lambda l: l["file"], licenses))))
		if docs != []:
			self.file.write("%%doc %s\n" % (" ".join(docs)))

		self.file.write("%endif\n")

	def generateChangelogSection(self):
		self.file.write("%changelog\n")

	def generate(self, artefact, file = sys.stdout):
		self.file = file
		ip_info = ImportPathParserBuilder().buildWithLocalMapping()

		commit = artefact["metadata"]["commit"]
		url = artefact["metadata"]["import_path"]

		repo_info = RepositoryInfo(ip_info)
		repo_info.retrieve(url, commit)

		provider = ip_info.getProvider()
		project = ip_info.getProject()
		repository = ip_info.getRepository()
		archive_dir = repo_info.getArchiveInfo().archive_dir
		prefix = ip_info.getPrefix()
		provider_prefix = ip_info.getProviderPrefix()

		# generate header
		self.generateHeaderEpilogue()

		# generate first level license and docs only
		licenses = filter(lambda l: len(l["file"].split("/")) == 1, artefact["data"]["licenses"])
		docs = filter(lambda l: len(l.split("/")) == 1, artefact["data"]["docs"])


		if provider == GITHUB:
			self.generateGithubHeader(project, repository, url, provider_prefix, commit, licenses)
		elif provider == GOOGLECODE:
			self.generateGooglecodeHeader(repository, url, provider_prefix, commit, licenses)
		elif provider == BITBUCKET:
			self.generateBitbucketHeader(project, repository, url, provider_prefix, commit, licenses)
		else:
			raise ValueError("Unknown provider")

		self.file.write("\n")
		self.generateHeaderPrologue(artefact["data"]["mains"], prefix)

		# generate devel subpackage
		self.generateDevelHeader(artefact["data"]["packages"], prefix)
		self.file.write("\n")

		# generate unit-test-devel subpackage
		self.generateUnitTestHeader(artefact["data"]["tests"], artefact["data"]["packages"], prefix)
		self.file.write("\n")

		# generate prep section
		self.generatePrepSection(provider)
		self.file.write("\n")

		# generate build section
		self.generateBuildSection(url, artefact["data"]["mains"])
		self.file.write("\n")

		# generate install section
		self.generateInstallSection(artefact["data"]["mains"], artefact["data"]["dependency_directories"])
		self.file.write("\n")

		# generate check section
		self.generateCheckSection(artefact["data"]["tests"])
		self.file.write("\n")

		# generate files section
		if url != provider_prefix:
			ip_prefix, _ = os.path.split(url)
		else:
			ip_prefix = ""

		self.generateFilesSection(provider, docs, licenses, artefact["data"]["mains"], ip_prefix)
		self.file.write("\n")

		# generate changelog section
		self.generateChangelogSection()
		self.file.write("\n")

		return True

	def setOutputFile(self, file):
		self.file = file

