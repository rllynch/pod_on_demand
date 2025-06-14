#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################

cd "$kohya_ss_dir"

if pgrep -f "gui.sh" > /dev/null ; then
    # Already Running
    echo "Kohya_ss gui.sh already running."
else
    # Not running
    echo "Starting Kohya_ss..."
    no_proxy="localhost, 127.0.0.1, ::1" nohup ./gui.sh --headless
    tail --retry -f nohup.out &
fi

iter=0
while [ 1 ]; do
    status=$(curl -Is http://127.0.0.1:7860 | head -1)

    if [[ $status == *"200 OK"* ]]; then
        echo "Kohya_ss is up and running."
        break
    fi

    if (( $iter % 15 == 0 )); then
        echo "Waiting for Kohya_ss to start..."
    fi
    sleep 1

    if [ $iter -ge 120 ]; then
        echo "Timeout: Kohya_ss failed to start after 120 seconds"
        exit 1
    fi

    iter=$((iter + 1))
done
