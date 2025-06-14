#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

rm -f ${model_size_fn}

${script_dir}/setup_os.sh
${script_dir}/setup_venv.sh
${script_dir}/setup_huggingface.sh
${script_dir}/setup_comfyui.sh
${script_dir}/setup_flux.sh
${script_dir}/setup_wan.sh

${script_dir}/setup_ollama.sh
${script_dir}/run_ollama.sh
${script_dir}/setup_ollama_models.sh

# ComfyUI may depend on the ollama Python package so run it after setting up Ollama
${script_dir}/run_comfyui.sh

${script_dir}/report_disk_usage.sh
