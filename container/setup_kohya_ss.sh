#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################
# Kohya's GUI
########################################################################################

apt install -y \
    python3-tk \
    python3-venv

mkdir -p "$kohya_ss_parent"
cd "$kohya_ss_parent"
#cd $install_root
if [ ! -d "$kohya_ss_dir" ]; then
    kohya_basename=$(basename "$kohya_ss_dir")
    git clone --recursive https://github.com/bmaltais/kohya_ss.git "$kohya_basename"
fi

cd "$kohya_ss_dir"
git pull
git submodule update --init --recursive
./setup-runpod.sh
