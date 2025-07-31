#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $SCRIPT_DIR

RSYNC="rsync -rtlv --delete"

# Backup everything that isn't checked out from git or a downloaded model
echo
echo "Building list of files to backup..."
ssh comfyui "/workspace/scripts/container/backup_paths.py" > backup_path_list.txt

echo
echo "Files to backup:"
cat backup_path_list.txt

# Build corresponding list of local files in backup directory
cd ../backup
find . -type f | sed -e 's/^\.//' > $SCRIPT_DIR/backup_path_list_local.txt

# Find local files not present in remote list
grep -Fxvf $SCRIPT_DIR/backup_path_list.txt $SCRIPT_DIR/backup_path_list_local.txt | cut -c 2- > $SCRIPT_DIR/backup_path_list_rm_local.txt || true

# Remove local files not present in remote list
if [ -s $SCRIPT_DIR/backup_path_list_rm_local.txt ]; then
    echo
    echo "Removing local files not present in remote backup list:"
    cat $SCRIPT_DIR/backup_path_list_rm_local.txt
    cat $SCRIPT_DIR/backup_path_list_rm_local.txt | xargs rm -f
fi

cd $SCRIPT_DIR
echo
echo "Backing up files to local backup directory..."
$RSYNC \
    --files-from=backup_path_list.txt \
    comfyui:/ \
    "$SCRIPT_DIR/../backup/"

rm -f backup_path_list.txt backup_path_list_local.txt backup_path_list_rm_local.txt

echo
echo "Backup completed successfully."
