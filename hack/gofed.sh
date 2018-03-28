#!/bin/sh

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# use config files from the repository
export GOFED_DEVEL=1
# set PYTHONPATH
export PYTHONPATH=${CUR_DIR}/../third_party/gofedlib:${CUR_DIR}/../third_party/gofed_resources:${CUR_DIR}/../../infra:${CUR_DIR}/../third_party/cmdsignature:${CUR_DIR}/../..
#export PYTHONPATH=/home/jchaloup/Projects/gofed/infra/third_party:/home/jchaloup/Projects/gofed:/home/jchaloup/Projects/gofed/gofed/third_party:/home/jchaloup/Projects/gofed
export ANSIBLE_CONFIG=/home/jchaloup/Projects/gofed/infra/ansible/ansible.cfg

${CUR_DIR}/../gofed $@
