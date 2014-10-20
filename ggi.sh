#!/bin/sh

script_dir=$(dirname $0)

$script_dir/getimports.sh $(tree -if | grep "[.]go$")
