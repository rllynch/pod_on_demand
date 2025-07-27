#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################
# vLLM
########################################################################################

# vLLM has requirements incompatible with the other packages so give it its own venv
mkdir -p /opt/vllm
cd /opt/vllm
if [ ! -d venv ]; then
    python3 -m venv venv
fi
. venv/bin/activate

pip install vllm openai
