#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

model=${1:-Qwen/Qwen3-8B}

. "${script_dir}/common.sh"

########################################################################################

export HF_TOKEN=$(cat /workspace/.cache/huggingface/token)

. /opt/vllm/venv/bin/activate

if [ "$model" == "meta-llama/Llama-3.1-8B-Instruct" ]; then
    python -m vllm.entrypoints.openai.api_server --model="meta-llama/Llama-3.1-8B-Instruct"

elif [ "$model" == "mistralai/Mistral-7B-Instruct-v0.3" ]; then
    mkdir -p /workspace/vllm/templates
    template=/workspace/vllm/templates/tool_chat_template_mistral.jinja
    if [ ! -f $template ]; then
        wget https://raw.githubusercontent.com/vllm-project/vllm/refs/heads/main/examples/tool_chat_template_mistral.jinja \
            -O $template
    fi

    vllm serve $model \
                --chat-template $template \
                --enable-auto-tool-choice \
                --tool-call-parser mistral

elif [ "$model" == "meta-llama/Llama-3.2-3B" ]; then
    # https://docs.vllm.ai/en/stable/features/tool_calling.html#llama-models-llama3_json
    mkdir -p /workspace/vllm/templates
    template=/workspace/vllm/templates/tool_chat_template_llama3.2_json.jinja
    if [ ! -f $template ]; then
        wget https://raw.githubusercontent.com/vllm-project/vllm/refs/heads/main/examples/tool_chat_template_llama3.2_json.jinja \
            -O $template
    fi

    vllm serve $model \
                --chat-template $template \
                --enable-auto-tool-choice \
                --tool-call-parser llama3_json

elif [ "$model" == "Qwen/Qwen3-8B" ]; then
    # https://qwen.readthedocs.io/en/latest/deployment/vllm.html
    # https://docs.vllm.ai/en/stable/features/tool_calling.html#qwen-models
    vllm serve $model \
                --enable-auto-tool-choice \
                --tool-call-parser hermes \
                --reasoning-parser qwen3 \
                --max_model_len 24576
fi
