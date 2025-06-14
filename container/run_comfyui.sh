#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################

cd ${install_root}/ComfyUI

if pgrep -f "main.py" > /dev/null ; then
    # Already Running
    echo "ComfyUI main.py already running."
else
    # Not running
    echo "Starting ComfyUI..."
    nohup python main.py --listen 127.0.0.1 --port 9020 &
    tail --retry -f nohup.out &

fi

iter=0
while [ 1 ]; do
    status=$(curl -Is http://127.0.0.1:9020 | head -1)

    if [[ $status == *"200 OK"* ]]; then
        echo "ComfyUI is up and running."
        break
    fi

    if (( $iter % 15 == 0 )); then
        echo "Waiting for ComfyUI to start..."
    fi
    sleep 1

    if [ $iter -ge 120 ]; then
        echo "Timeout: ComfyUI failed to start after 120 seconds"
        exit 1
    fi

    iter=$((iter + 1))
done
