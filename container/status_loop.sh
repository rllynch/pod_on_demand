#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

while [ 1 ] ; do
    echo "---nvidia-smi"
    nvidia-smi --query-gpu=index,utilization.gpu --format=csv,noheader,nounits

    echo "---top"
    # Top in batch mode, 30 seconds delay between iterations, 2 iterations
    # First iteration will have CPU usage since boot, second will have CPU usage for last 30 seconds
    top -b -d 30 -n 2 | grep "^ "

    echo "---sleep"
    sleep 1
done
