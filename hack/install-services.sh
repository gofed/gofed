#!/bin/sh

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cp daemons/*.service /usr/lib/systemd/user/.
