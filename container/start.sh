#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

echo "$0 is starting"

echo "Running ${script_dir}/setup.sh ..."
${script_dir}/setup.sh

echo "Running /start.sh ..."
/start.sh

# Should never reach here
echo "$0 has finished"

