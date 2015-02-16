%global provider        github
%global provider_tld    com
%global project        	ingvagabund
%global repo            GolangPackageGenerator
%global commit		99ec1aad9367ee1482e9386dd9db4969d1ed9130
%global shortcommit	%(c=%{commit}; echo ${c:0:7})

Name:		go2fed
Version:	0
Release:	11%{?dist}
Summary:	Tool for development of golang devel packages
License:	GPLv2+
URL:		https://github.com/ingvagabund/GolangPackageGenerator
Source0:	https://github.com/ingvagabund/GolangPackageGenerator/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz

Requires: python >= 2.7.5, bash, wget, rpmdevtools, rpmlint
Requires: fedpkg, koji, coreutils, rpm-build, openssh-clients, tar
Requires: python-PyGithub, bash-completion

%description
Tool to automize packaging of golang devel source codes.
The main goal is to automatize packaging (spec file generator),
dependency discovering, testing (scratch builds), to prepare package review.
If possible, all in one command.

%prep
%setup -q -n %{repo}-%{commit}

%build

%install
# copy bash completition
mkdir -p %{buildroot}/etc/bash_completion.d/
./gen_bash_completion.sh %{name} > %{buildroot}/etc/bash_completion.d/%{name}
# copy man page
mkdir -p %{buildroot}/usr/share/man/man1
cp man/go2fed-help.1 %{buildroot}/usr/share/man/man1/go2fed.1
# copy scripts
mkdir -p %{buildroot}/usr/share/%{name}
cp *.sh %{buildroot}/usr/share/%{name}/.
cp *.py %{buildroot}/usr/share/%{name}/.
cp -r modules %{buildroot}/usr/share/%{name}/.
# copy config
mkdir -p %{buildroot}/usr/share/%{name}/config
cp config/go2fed.conf %{buildroot}/usr/share/%{name}/config/.
# copy golang list and native imports
cp -r data %{buildroot}/usr/share/%{name}/.
# copy the tool script
cp %{name} %{buildroot}/usr/share/%{name}/.

%post
if [ "$1" -eq 1 ]; then
	# make a symlink to go2fed
	ln -s /usr/share/%{name}/%{name} /usr/bin/%{name}
fi

%preun
if [ "$1" -eq 0 ]; then
	rm /usr/bin/%{name}
fi

%files
%doc README.md LICENSE
%config /usr/share/%{name}/config/go2fed.conf
/etc/bash_completion.d/%{name}
/usr/share/%{name}
/usr/share/man/man1/go2fed.1.gz

%changelog
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


