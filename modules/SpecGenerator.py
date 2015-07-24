from ImportPath import GITHUB, GOOGLECODE, GOOGLEGOLANGORG, GOLANGORG, GOPKG, BITBUCKET, UNKNOWN
from PackageInfo import PackageInfo
from ProviderPrefixes import ProviderPrefixes
import os
from Utils import runCommand

class SpecGenerator:

	def __init__(self, import_path, commit="", skiperrors=False):		
		self.import_path = import_path
		self.commit = commit
		self.spec_name = ""
		self.pkg_info = None
		self.warn = ""

	def getWarning(self):
		return self.warn

	def setPackageInfo(self, pkg_info):
		self.pkg_info = pkg_info

	def generateHeaderEpilogue(self):
		self.file.write("%if 0%{?fedora}\n")
		self.file.write("%global with_devel 1\n")
		self.file.write("%global with_bundled 0\n")
		self.file.write("%global with_debug 0\n")
		self.file.write("%global with_check 1\n")
		self.file.write("%else\n")
		self.file.write("%global with_devel 0\n")
		self.file.write("%global with_bundled 1\n")
		self.file.write("%global with_debug 0\n")
		self.file.write("%global with_check 0\n")
		self.file.write("%endif\n\n")

		# debug
		self.file.write("%if 0%{?with_debug}\n")
		self.file.write("%global _dwz_low_mem_die_limit 0\n")
		self.file.write("%else\n")
		self.file.write("%global debug_package   %{nil}\n")
		self.file.write("%endif\n\n")

	def generateGithubHeader(self, project, repository, url, provider_prefix, commit):
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
		self.file.write("License:        !!!!FILL!!!!\n")
		self.file.write("URL:            https://%{provider_prefix}\n")
		self.file.write("Source0:        https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz\n")

	def generateGooglecodeHeader(self, repository, url, provider_prefix, commit):
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
		self.file.write("License:        !!!!FILL!!!!\n")
		self.file.write("URL:            https://%{provider_prefix}\n")
		self.file.write("Source0:        https://%{rrepo}.%{provider}%{provider_sub}.%{provider_tld}/archive/%{rev}.tar.gz\n")

	def generateBitbucketHeader(self, project, repository, url, provider_prefix, commit):
		self.file.write("%global provider        bitbucket\n")
		self.file.write("%global provider_tld    org\n")
		self.file.write("%%global project         %s\n" % project)
		self.file.write("%%global repo            %s\n" % repository)
		self.file.write("# https://%s\n" % provider_prefix)
		self.file.write("%%global provider_prefix     %s\n", provider_prefix)
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
		self.file.write("URL:            https://%{provider_prefix}\n")
		self.file.write("Source0:        https://%{provider_prefix}/get/%%{shortcommit}.tar.gz\n")

	def generateHeaderPrologue(self):
		self.file.write("\n%if 0%{?fedora} >= 19 || 0%{?rhel} >= 7\n")
                self.file.write("BuildArch:      noarch\n")
                self.file.write("%else\n")
                self.file.write("ExclusiveArch:  %{ix86} x86_64 %{arm}\n")
                self.file.write("%endif\n")
                self.file.write("\n")
                self.file.write("%description\n")
                self.file.write("%{summary}\n")
                self.file.write("\n")

	def generateDevelHeader(self, project, prefix):
		self.file.write("%if 0%{?with_devel}\n")
                self.file.write("%package devel\n")
                self.file.write("Summary:       %{summary}\n")
                self.file.write("\n")

		# dependencies
		imported_packages = project.getImportedPackages()
		self.file.write("BuildRequires: golang >= 1.2.1-3\n")
		for dep in imported_packages:
			if dep.startswith(prefix):
				continue

			self.file.write("BuildRequires: golang(%s)\n" % (dep))

		if imported_packages != []:
			self.file.write("\n")
			for dep in imported_packages:
				if dep.startswith(prefix):
					continue

				self.file.write("Requires:      golang(%s)\n" % (dep))

		# provides
		self.file.write("\n")
		for path in project.getProvidedPackages():
			sufix = ""
			if path != ".":
				sufix = "/%s" % path

			self.file.write("Provides:      golang(%%{import_path}%s) = %%{version}-%%{release}\n" % sufix)

		# description
		self.file.write("\n%description devel\n")
		self.file.write("%{summary}\n\n")
		self.file.write("This package contains library source intended for\n")
		self.file.write("building other packages which use %{project}/%{repo}.\n")
		self.file.write("%endif\n")

	def generatePrepSection(self, provider):
		self.file.write("%prep\n")

		if provider == GOOGLECODE:
			self.file.write("%setup -q -n %{rrepo}-%{shortrev}\n")
		elif provider == BITBUCKET:
			self.file.write("%setup -q -n %{project}-%{repo}-%{shortcommit}\n")
		else:
			self.file.write("%setup -q -n %{repo}-%{commit}\n")

	def generateBuildSection(self):
		self.file.write("%build\n")

	def generateInstallSection(self, direct_go_files = False):
		self.file.write("%install\n")
		self.file.write("%if 0%{?with_devel}\n")
		self.file.write("install -d -p %{buildroot}/%{gopath}/src/%{import_path}/\n")
 
		# go files in tarball_path?
		if direct_go_files:
			self.file.write("cp -pav *.go %{buildroot}/%{gopath}/src/%{import_path}/\n")

		# read all dirs in the tarball
		self.file.write("\n# copy directories\n")
		self.file.write("for file in ./* ; do\n")
		self.file.write("    if [ -d $file ]; then\n")
		self.file.write("        cp -rpav $file %{buildroot}%{gopath}/src/%{import_path}/\n")
		self.file.write("    fi\n")
		self.file.write("done\n")
		self.file.write("%endif\n")

	def generateCheckSection(self, project):
		self.file.write("%check\n")
		self.file.write("%if 0%{?with_check}\n")
		self.file.write("export GOPATH=%{buildroot}/%{gopath}:%{gopath}\n")

		sdirs = sorted(project.getTestDirectories())
                for dir in sdirs:

			sufix = ""
			if dir != ".":
				sufix = "/%s" % dir

			self.file.write("go test %%{import_path}%s\n" % sufix)
		self.file.write("%endif\n")

	def generateFilesSection(self, provider, project, ip_prefix = ""):
		self.file.write("%if 0%{?with_devel}\n")
		self.file.write("%files devel\n")

		# doc all *.md files
		docs = project.getDocs()
		if docs != []:
			# scan for license
			licenses = []
			restdocs = []
			for doc in docs:
				if doc.lower().find('license') != -1:
					licenses.append(doc)
				elif doc.lower().find('copying') != -1:
					licenses.append(doc)
				else:
					restdocs.append(doc)

			# %license tag is supported since rpm-4.11, it means on fedora and epel7, not epel6
			# as epel7 is not supposed to have any golang packages, using %license only for fedora
			self.file.write("%if 0%{?fedora}\n")
			self.file.write("%%license %s\n" % (" ".join(licenses)))
			self.file.write("%else\n")
			self.file.write("%%doc %s\n" % (" ".join(licenses)))
			self.file.write("%endif\n")
			self.file.write("%%doc %s\n" % (" ".join(restdocs)))

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

		self.file.write("%{gopath}/src/%{import_path}\n")
		self.file.write("%endif\n")

	def generateChangelogSection(self):
		self.file.write("%changelog\n")

	def generate(self):
		if self.pkg_info == None:
			self.err = "PackageInfo not set"
			return False

		cwd = os.getcwd()
		repo_info = self.pkg_info.getRepositoryInfo()
		archive_info = repo_info.getArchiveInfo()
		ip_info = repo_info.getImportPathInfo()
		prj_info = self.pkg_info.getProjectInfo()

		self.warn = prj_info.getWarning()

		provider = ip_info.getProvider()
		project = ip_info.project
		repository = ip_info.repository
		commit = repo_info.getCommit()
		url = ip_info.getPrefix()
		archive_dir = archive_info.archive_dir
		prefix = ip_info.getPrefix()
		provider_prefix = ip_info.getProviderPrefix()

		# generate header
		self.generateHeaderEpilogue()

		if provider == GITHUB:
			self.generateGithubHeader(project, repository, url, provider_prefix, commit)
		elif provider == GOOGLECODE:
			self.generateGooglecodeHeader(repository, url, provider_prefix, commit)
		elif provider == BITBUCKET:
			self.generateBitbucketHeader(project, repository, url, provider_prefix, commit)

		self.generateHeaderPrologue()

		# generate devel subpackage
		self.generateDevelHeader(prj_info, prefix)
		self.file.write("\n")

		# generate prep section
		self.generatePrepSection(provider)
		self.file.write("\n")

		# generate build section
		self.generateBuildSection()
		self.file.write("\n")

		# generate install section
		direct_go_files = False
		if "." in prj_info.getProvidedPackages():
			direct_go_files = True

		self.generateInstallSection(direct_go_files)
		self.file.write("\n")

		# generate check section
		self.generateCheckSection(prj_info)
		self.file.write("\n")

		# generate files section
		if url != provider_prefix:
			ip_prefix, _ = os.path.split(url)
		else:
			ip_prefix = ""

		self.generateFilesSection(provider, prj_info, ip_prefix)
		self.file.write("\n")

		# generate changelog section
		self.generateChangelogSection()
		self.file.write("\n")

		return True

	def setOutputFile(self, file):
		self.file = file

