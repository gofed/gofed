#!/bin/sh

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# remove rendered templates
rm -f ${CUR_DIR}/daemons/*.service

# remove infra->gofed_infra symlink
rm -f ${CUR_DIR}/../third_party/infra
