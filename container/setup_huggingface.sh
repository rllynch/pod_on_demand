#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################
# huggingface-cli
########################################################################################

cd $script_dir

pip install -U "huggingface_hub[cli]"

git config --global credential.helper store

if [ ! -f ${HF_HOME}/token ]; then
    huggingface-cli login
fi
