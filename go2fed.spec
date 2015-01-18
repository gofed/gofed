%global commit		116cd7b98fe82a78c388f3c1cd79402aaea4d7c6
%global shortcommit	%(c=%{commit}; echo ${c:0:7})

Name:		go2fed
Version:	0
Release:	1%{?dist}
Summary:	Tool for development of golang devel packages
License:	GPLv2+
URL:		https://github.com/ingvagabund/GolangPackageGenerator
Source0:	https://github.com/ingvagabund/GolangPackageGenerator/archive/%{commit}/gpg-%{shortcommit}.tar.gz

Requires: python >= 2.7.5, bash, wget, rpmdevtools, rpmlint
Requires: fedpkg, koji, coreutils, rpm-build, openssh-clients, tar
Requires: python-PyGithub, bash-completion

%description
Tool to automize packaging of golang devel source codes.
The main goal is to automatize packaging (spec file generator),
dependency discovering, testing (scratch builds), to prepare package review.
If possible, all in one command.

%prep
%setup -q -n GolangPackageGenerator-%{commit}

%build

%install
# copy bash completition
mkdir -p %{buildroot}/etc/bash_completion.d/
cp completions/bash/go2fed %{buildroot}/etc/bash_completion.d/.
# copy man page
mkdir -p %{buildroot}/usr/share/man/man1
cp man/go2fed-help.1 %{buildroot}/usr/share/man/man1/go2fed.1.gz
# copy scripts
mkdir -p %{buildroot}/usr/share/go2fed
cp *.sh %{buildroot}/usr/share/go2fed/.
cp *.py %{buildroot}/usr/share/go2fed/.
# copy config
mkdir -p %{buildroot}/usr/share/go2fed/config
cp config/go2fed.conf %{buildroot}/usr/share/go2fed/config/.
# copy golang list and native imports
cp golang.list golang.imports %{buildroot}/usr/share/go2fed/.
# copy the tool script
cp go2fed %{buildroot}/usr/share/go2fed/.

%post
# make a symlink to go2fed
ln -s /usr/share/go2fed/go2fed /usr/bin/go2fed

%preun
rm /usr/bin/go2fed

%files
%doc README.md LICENSE
/etc/bash_completion.d/go2fed
%dir /usr/share/go2fed
/usr/share/go2fed/*
%config /usr/share/go2fed/config
/usr/share/man/man1/go2fed.1.gz

%changelog
* Fri Oct 24 2014 jchaloup <jchaloup@redhat.com>
- Initial package


