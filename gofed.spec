%global debug_package   %{nil}
%global provider        github
%global provider_tld    com
%global project        	ingvagabund
%global repo            gofed
%global commit		3b5f0811a4c77ae5abeac2f8f1327618db038494
%global shortcommit	%(c=%{commit}; echo ${c:0:7})

Name:		gofed
Version:	0
Release:	20%{?dist}
Summary:	Tool for development of golang devel packages
License:	GPLv2+
URL:		https://github.com/ingvagabund/GolangPackageGenerator
Source0:	https://github.com/ingvagabund/GolangPackageGenerator/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz

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
go build parseGo.go

%install
# copy bash completition
mkdir -p %{buildroot}/etc/bash_completion.d/
./gen_bash_completion.sh %{name} > %{buildroot}/etc/bash_completion.d/%{name}
# copy man page
mkdir -p %{buildroot}/usr/share/man/man1
cp man/gofed-help.1 %{buildroot}/usr/share/man/man1/gofed.1
# copy scripts
mkdir -p %{buildroot}/usr/share/%{name}
cp *.sh %{buildroot}/usr/share/%{name}/.
cp *.py %{buildroot}/usr/share/%{name}/.
cp -r modules %{buildroot}/usr/share/%{name}/.
cp parseGo %{buildroot}/usr/share/%{name}/.
# copy config
mkdir -p %{buildroot}/usr/share/%{name}/config
cp config/gofed.conf %{buildroot}/usr/share/%{name}/config/.
# copy golang list and native imports
cp -r data %{buildroot}/usr/share/%{name}/.
# copy the tool script
cp %{name} %{buildroot}/usr/share/%{name}/.
# directory for local database
mkdir -p %{buildroot}/var/lib/%{name}
chmod 0777 %{buildroot}/var/lib/%{name}

%post
if [ "$1" -eq 1 ]; then
	# make a symlink to gofed
	ln -s /usr/share/%{name}/%{name} /usr/bin/%{name}
fi

%preun
if [ "$1" -eq 0 ]; then
	rm /usr/bin/%{name}
fi

%files
%doc README.md LICENSE
%config /usr/share/%{name}/config/gofed.conf
/etc/bash_completion.d/%{name}
/usr/share/%{name}
/usr/share/man/man1/gofed.1.gz
/var/lib/%{name}

%changelog
* Thu Mar 12 2015 jchaloup <jchaloup@redhat.com> - 0-20
- Bump to upstream 3b5f0811a4c77ae5abeac2f8f1327618db038494

* Wed Mar 11 2015 jchaloup <jchaloup@redhat.com> - 0-19
- Bump to upstream a655e365927782128ba55b7aed8d45bd24607e6c

* Wed Mar 04 2015 jchaloup <jchaloup@redhat.com> - 0-18
- Bump to upstream a257a2ff395a2d2bbdf26a7c4158a451332a9331

* Sat Feb 28 2015 jchaloup <jchaloup@redhat.com> - 0-17
- Bump to upstream a9bf0df51ab014dba5b7da8f79dc656772cff249

* Fri Feb 20 2015 jchaloup <jchaloup@redhat.com> - 0-16
- Bump to upstream 78df015bc5191022fd905eb367f59d087b0d5f7f

* Fri Feb 20 2015 jchaloup <jchaloup@redhat.com> - 0-15
- Bump to upstream 6e2988a737e5fd9eb6dcc5176616dada75c2f1c3

* Fri Feb 20 2015 jchaloup <jchaloup@redhat.com> - 0-14
- Bump to upstream 173ae3e5765d816bcd8f75549df2f6cedfa54727

* Thu Feb 19 2015 jchaloup <jchaloup@redhat.com> - 0-13
- Bump to upstream 0eeacb4af7558fe754c08b693f262d43fb575fee

* Wed Feb 18 2015 jchaloup <jchaloup@redhat.com> - 0-12
- Bump to upstream 4d257eb9b58a9cd3f554b1bfbb6255c2beda0282

* Mon Feb 16 2015 jchaloup <jchaloup@redhat.com> - 0-11
- Bump to upstream 99ec1aad9367ee1482e9386dd9db4969d1ed9130

* Wed Feb 11 2015 jchaloup <jchaloup@redhat.com> - 0-10
- Bump to upstream bb8cc08c193bfa34287fdbc2ee132f36b811f41c

* Tue Feb 10 2015 jchaloup <jchaloup@redhat.com> - 0-9
- Bump to upstream 1d0006008ddacaf7e143c47abc5f356bf61b5288

* Tue Feb 10 2015 jchaloup <jchaloup@redhat.com> - 0-8
- Bump to upstream 0da9d0676ec39c8555178c0d5e483fbba8b8613f

* Tue Feb 10 2015 jchaloup <jchaloup@redhat.com> - 0-7
- Bump to upstream 8608cdba646113dbc31ac1edd47cf06c86fa13c6

* Mon Feb 09 2015 jchaloup <jchaloup@redhat.com> - 0-6
- Bump to upstream cd28b3a544b2af7de49dc90072266d60c4365e94

* Mon Feb 09 2015 jchaloup <jchaloup@redhat.com> - 0-5
- Bump to upstream a16c74d5be4afc693d9c4d2a4ff069199f9927e6

* Mon Feb 09 2015 jchaloup <jchaloup@redhat.com> - 0-4
- Bump to upstream 46db1fa5e7c380cd7eddd87c0bb9f1675b8992ea

* Mon Feb 09 2015 jchaloup <jchaloup@redhat.com> - 0-3
- Bump to upstream f6bbc7c683601e6cbd4bd3c3bceeb616e840511b

* Mon Feb 09 2015 jchaloup <jchaloup@redhat.com> - 0-2
- Bump to upstream 6a1b91cb818b88e0c40f68b6c8a3bd2ab75b6340

* Fri Oct 24 2014 jchaloup <jchaloup@redhat.com>
- Initial package


