#!/bin/sh

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# use config files from the repository
export GOFED_DEVEL=1
# set PYTHONPATH
export PYTHONPATH=${CUR_DIR}/../third_party:${CUR_DIR}/../..

${CUR_DIR}/../gofed $@
