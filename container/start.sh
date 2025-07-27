#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

ln -sf "${script_dir}/post_start.sh" "/post_start.sh"

echo "Running /start.sh ..."
/start.sh

# Should never reach here
echo "$0 has finished"
