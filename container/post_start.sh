#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

# Need to handle /post_start.sh being a symlink and resolve to the actual script location
script_dir=$( cd -- "$( dirname -- "$(readlink -f ${BASH_SOURCE[0]})" )" &> /dev/null && pwd )

rm -f "${script_dir}/.env.sh"
. "${script_dir}/common.sh"

echo "$0 is starting"

cat << EOF > "${script_dir}/.env.sh"
export MODELS="$MODELS"
export SETUP_SCRIPTS="$SETUP_SCRIPTS"
EOF

echo "Running ${script_dir}/setup.sh ..."
${script_dir}/setup.sh

echo "$0 has finished"
