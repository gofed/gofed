FROM	fedora:23
MAINTAINER Jan Chaloupka <jchaloup@redhat.com>

LABEL Name="gofed" \
      Version="v1.0.0"

# install gofed deps
RUN dnf install -y git python-pip graphviz koji rpm-build rpmdevtools && dnf clean all

# create gofed user for workplace
RUN useradd gofed

RUN cd /home/gofed && \
    git clone https://github.com/gofed/gofed && \
    cd gofed && \
    pip install -r requirements.txt && \
    ./hack/prep.sh

RUN cd /home/gofed/gofed && echo "alias gofed=$(realpath ./hack/gofed.sh)" >> ~/.bashrc

# set entrypoint
CMD ["gofed"]

