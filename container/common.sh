#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

common_script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${common_script_dir}/config.sh"

download_hf_model() {
    local model="$1"
    local subdir="$2"
    local repo="$3"

    # If repo starts with "https://" then split into parts
    if [[ "$repo" == https://huggingface.co/* ]]; then
        # Extract the repo name from the URL
        repo=${repo#https://huggingface.co/}
        # Split on /resolve/main/
        local server_path="${repo#*/resolve/main/}"
        repo=${repo%%/resolve/main/*}
        # Split on final /
        local filename="${server_path##*/}"
    else
        local server_path="$4"
        local filename=$(basename "$server_path")
    fi

    local local_dir="${install_root}/ComfyUI/models/${subdir}/"
    local local_path="${local_dir}/${filename}"

    if [[ ":$MODELS:" == *":$model:"* ]]; then
        # MODELS env var contains this model
        local action="install"
    else
        local action="uninstall"
    fi

    echo "[$action] $model: $filename"

    if [ "$action" == "uninstall" ]; then
        if [ -f "$local_path" ]; then
            # Resolve source of symlink
            local cache_path1=$(readlink -f "$local_path")
            local cache_path2=$(readlink -f "$cache_path1")
            rm -f "$local_path"
            rm -f "$cache_path1"
            rm -f "$cache_path2"
        fi
        return
    fi
    cd $local_dir
    if [ -f "$local_path" ]; then
        echo "Model already exists: $filename"
    else
        ln -sf $(hf download "$repo" "$server_path")
    fi

    local real_path=$(realpath "$local_path")
    local size=$(du -bs "$real_path" | awk '{printf("%4.1f GB\n", $1/2^30)}')
    echo "${size} ${filename}" >> ${model_size_fn}
}

if [ -n "$venv_dir" ] && [ -f "$venv_dir/bin/activate" ]; then
    . "$venv_dir/bin/activate"
fi
