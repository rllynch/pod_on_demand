#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

"${script_dir}/backup_paths.py" > /tmp/backup_paths.txt

# Merge list of files from backup_remote into list in case anything was deleted
rclone ls backup_remote:backup | sed -re 's/^\s*[0-9]+ /\//' >> /tmp/backup_paths.txt
cat /tmp/backup_paths.txt | sort | uniq > /tmp/backup_paths.dedup.txt
mv /tmp/backup_paths.dedup.txt /tmp/backup_paths.txt

rclone sync --copy-links --verbose --files-from /tmp/backup_paths.txt / backup_remote:backup
rm -f /tmp/backup_paths.txt

echo "Backup completed successfully."
