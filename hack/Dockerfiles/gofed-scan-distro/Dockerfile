FROM	gofed/gofed:v1.0.1
MAINTAINER Jan Chaloupka <jchaloup@redhat.com>

LABEL Name="gofed-scan-distro" \
      Version="v1.0.1"

# install deps for koji authentication
COPY fedora-updates-f25.repo /etc/yum.repos.d/fedora-updates-f25.repo
RUN dnf install -y --enablerepo=f25updates fedpkg fedora-packager pyrpkg koji python2-cccolutils krb5-workstation

RUN pip install requests==2.3
COPY krb5.conf /etc/krb5.conf
COPY run-scan.sh /home/gofed/gofed/run-scan.sh

# set entrypoint
CMD ["gofed"]

