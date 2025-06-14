#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################
# ComfyUI
########################################################################################

cd $install_root
if [ ! -d ComfyUI ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git
fi

cd ComfyUI
git pull
pip install -r requirements.txt

########################################################################################
# ComfyUI-Manager
########################################################################################

cd ${install_root}/ComfyUI/custom_nodes
if [ ! -d comfyui-manager ]; then
    git clone https://github.com/ltdrdata/ComfyUI-Manager comfyui-manager
fi

cd comfyui-manager
git pull
