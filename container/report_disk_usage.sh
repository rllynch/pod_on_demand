#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################
# Report sizes
########################################################################################

echo "===================================================================="
cat "$model_size_fn" | sort -n

echo "===================================================================="
du -hsc /workspace

rm -f "$model_size_fn"
