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
    echo "rsync'ing home directory from ${install_root}/home to /root"

    # This needs to happen after installing $extra_apt_packages
    # Additionally, extra_apt_packages must contain rsync
    rsync -rltv \
        "${install_root}/home/" /root/
else
    echo "No home directory found at ${install_root}/home, skipping rsync."
fi
