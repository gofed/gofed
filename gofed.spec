%global _dwz_low_mem_die_limit 0
%global provider        github
%global provider_tld    com
%global project        	ingvagabund
%global repo            gofed
%global commit		a4c915e2a742578caf792158305c7d19a8e2c764
%global shortcommit	%(c=%{commit}; echo ${c:0:7})

Name:		gofed
Version:	0.0.1
Release:	0.1.git%{shortcommit}%{?dist}
Summary:	Tool for development of golang devel packages
License:	GPLv2+
URL:		https://github.com/%{project}/%{repo}
Source0:	https://github.com/%{project}/%{repo}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz
ExclusiveArch:  %{ix86} x86_64 %{arm}

BuildRequires: golang
Requires: python >= 2.7.5, bash, wget, rpmdevtools, rpmlint
Requires: fedpkg, koji, coreutils, rpm-build, openssh-clients, tar
Requires: python-PyGithub, bash-completion
Requires: graphviz

%description
Tool to automize packaging of golang devel source codes.
The main goal is to automatize packaging (spec file generator),
dependency discovering, testing (scratch builds), to prepare package review.
If possible, all in one command.

%prep
%setup -q -n %{repo}-%{commit}

%build
function gobuild { go build -a -ldflags "-B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \n')" -v -x "$@"; }
gobuild parseGo.go

%install
# copy bash completition
mkdir -p %{buildroot}/etc/bash_completion.d/
./gen_bash_completion.sh %{name} > %{buildroot}/etc/bash_completion.d/%{name}
# copy man page
mkdir -p %{buildroot}/usr/share/man/man1
cp man/gofed-help.1 %{buildroot}/usr/share/man/man1/gofed.1
# copy scripts
mkdir -p %{buildroot}/usr/share/%{name}
cp bitbucket2gospec.sh gen_bash_completion.sh github2gospec.sh \
   googlecode2gospec.sh %{buildroot}/usr/share/%{name}/.
cp *.py %{buildroot}/usr/share/%{name}/.
cp -r modules %{buildroot}/usr/share/%{name}/.
cp parseGo %{buildroot}/usr/share/%{name}/.
# copy config
mkdir -p %{buildroot}/usr/share/%{name}/config
cp config/gofed.conf %{buildroot}/usr/share/%{name}/config/.
# copy golang list and native imports
cp -r data %{buildroot}/var/lib/%{name}/.
# copy the tool script
cp %{name} %{buildroot}/usr/share/%{name}/.
# directory for local database
mkdir -p %{buildroot}/var/lib/%{name}
install -m 755 -d %{buildroot}/var/lib/%{name}
install -m 755 -d %{buildroot}/usr/bin
ln -s /usr/share/%{name}/%{name} %{buildroot}/usr/bin/%{name}
# symlinks
cp build gcp pull push scratch-build update bbobranches %{buildroot}/usr/share/%{name}/.

%files
%doc README.md LICENSE
%config(noreplace) /usr/share/%{name}/config/gofed.conf
/etc/bash_completion.d/%{name}
/usr/share/%{name}
/usr/share/man/man1/gofed.1.gz
/var/lib/%{name}
/usr/bin/%{name}

%check
function gofed { %{buildroot}/usr/share/%{name}/%{name} "$@" --dry; }
gofed scratch-build
gofed build
gofed pull
gofed push
gofed update
gofed gcpmaster
gofed tools --git-reset
gofed tools --bbo --dry test
gofed tools --bbo --wait --dry test
gofed tools --waitbbo --dry test
gofed wizard --scratch --dry

%changelog
* Thu Apr 02 2015 jchaloup <jchaloup@redhat.com> - 0.0.1-0.1.gita4c915e
- Initial commit for Fedora

