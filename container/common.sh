#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

common_script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${common_script_dir}/config.sh"

download_hf_model() {
    local subdir="$1"
    local repo="$2"
    local server_path="$3"
    local filename=$(basename "$server_path")

    local local_dir="${install_root}/ComfyUI/models/${subdir}/"
    local local_path="${local_dir}/${filename}"

    cd $local_dir
    if [ -f "$local_path" ]; then
        echo "Model already exists: $filename"
    else
        ln -sf $(huggingface-cli download "$repo" "$server_path")
    fi

    local real_path=$(realpath "$local_path")
    local size=$(du -bs "$real_path" | awk '{printf("%4.1f GB\n", $1/2^30)}')
    echo "${size} ${filename}" >> ${model_size_fn}
}

if [ -n "$venv_dir" ] && [ -f "$venv_dir/bin/activate" ]; then
    . "$venv_dir/bin/activate"
fi
