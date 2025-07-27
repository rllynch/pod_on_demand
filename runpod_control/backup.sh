#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eux

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $SCRIPT_DIR

RSYNC="rsync -rtlv --delete"

# Backup everything that isn't checked out from git or a downloaded model
ssh comfyui "/workspace/scripts/container/backup_paths.py" > backup_path_list.txt
$RSYNC comfyui:/ --files-from=backup_path_list.txt "$SCRIPT_DIR/../backup/"
rm -f backup_path_list.txt
