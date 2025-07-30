#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################

if [ ! -f /root/.apt_update_was_run ]; then
    apt update
    touch /root/.apt_update_was_run
fi

apt install -y $extra_apt_packages

if [ $do_apt_upgrade -ne 0 ]; then
    apt upgrade -y
fi

if [ -d "${install_root}/home" ]; then
    # Create symlinks from /root to /workspace/home for files like .vimrc, .gitconfig, etc.
    # This will create a symlink for each file so it's not suitable for symlinking
    # .cache, .config, etc.
    lndir /workspace/home/ /root/
else
    echo "No home directory found at ${install_root}/home, skipping creating symlinks."
fi

# This is mostly for interactive use - HF_HOME and PIP_CACHE_DIR already point at /workspace/.cache
rm -rf /root/.cache
ln -sf /workspace/.cache /root/.cache

# This is primarily for rclone's config
rm -rf /root/.config
ln -sf /workspace/.config /root/.config
