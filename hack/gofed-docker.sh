#!/bin/sh

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# set PYTHONPATH
export PYTHONPATH=${CUR_DIR}/../third_party:${CUR_DIR}/../third_party/cmdsignature:${CUR_DIR}/../..

${CUR_DIR}/../gofed-docker $@
