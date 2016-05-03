#!/bin/sh

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cp ${CUR_DIR}/daemons/*.service /usr/lib/systemd/user/.
