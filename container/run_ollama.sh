#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################

export OLLAMA_MODELS=${install_root}/ollama/models
export OLLAMA_HOST="127.0.0.1:11434"

export PATH=${install_root}/ollama/bin:$PATH
export LD_LIBRARY_PATH=${install_root}/ollama/lib:${LD_LIBRARY_PATH:-}

if pgrep -x "ollama" > /dev/null ; then
    # Already Running
    echo "Ollama is already running."
else
    # Not running
    echo "Starting Ollama server..."
    nohup ollama serve 2> /dev/null > /dev/null < /dev/null &
    if [ "${TAIL_LOGS:-1}" -eq 1 ]; then
        tail --retry -f nohup.out &
    fi
    sleep 5
fi

########################################################################################
# Pull models

for model in \
    "llama3.2:latest" \
    "gemma3:latest"
do
    ollama pull $model
done
