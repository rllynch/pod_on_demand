#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

rclone copy --copy-links --verbose backup_remote:backup /

if [ -d "/workspace/home" ]; then
    # Create symlinks from /root to /workspace/home for files like .vimrc, .gitconfig, etc.
    # This will create a symlink for each file so it's not suitable for symlinking
    # .cache, .config, etc.
    lndir /workspace/home/ /root/
fi

echo "Restore completed successfully."
