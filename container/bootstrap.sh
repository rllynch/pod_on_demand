#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

# Bootstrap a pod with an empty /workspace

set -eu
set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

rm -rf /workspace/.cache /workspace/.config
mv $script_dir/../backup/workspace/.cache  /workspace/.cache
mv $script_dir/../backup/workspace/.config /workspace/.config

GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no" git clone "$BOOTSTRAP_REPO" /workspace/scripts

cd /workspace/scripts/container
./setup.sh
./restore_from_rclone.sh
./run.sh

echo "bootstrap.sh complete"
