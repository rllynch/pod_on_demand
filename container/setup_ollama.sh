#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################
# Ollama
########################################################################################

mkdir -p ${install_root}/ollama
cd ${install_root}/ollama
if [ ! -f ollama-linux-amd64.tgz ]; then
    curl -L https://ollama.com/download/ollama-linux-amd64.tgz -o ollama-linux-amd64.tgz
fi

if [ ! -f ${install_root}/ollama/bin/ollama ]; then
    tar -C ${install_root}/ollama -xvzf ollama-linux-amd64.tgz
fi

ln -sf ${install_root}/ollama/bin/ollama /usr/local/bin/ollama

pip install -U ollama
