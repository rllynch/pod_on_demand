#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

import time
import json
import subprocess

import psutil

def get_gpu_stats():
    proc = subprocess.run([
        'nvidia-smi',
        '--query-gpu=index,utilization.gpu,memory.used',
        '--format=csv,noheader,nounits'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        raise RuntimeError(f"nvidia-smi failed with error: {proc.stderr.decode('utf-8')}")

    total_util = 0
    total_mem_gb = 0
    for line in proc.stdout.decode('utf-8', errors='ignore').splitlines():
        index, util, mem_mb = line.replace(',', ' ').split()
        total_util += float(util)
        total_mem_gb += float(mem_mb) / 1024
    return total_util, total_mem_gb

def main():
    while True:
        cpu_util = sum([proc.info['cpu_percent'] for proc in psutil.process_iter(['cpu_percent'])])
        # 10 ** 9 matches up with Runpod's web interface better than 2 ** 30
        cpu_mem_gb = sum([proc.info['memory_info'].rss for proc in psutil.process_iter(['memory_info'])]) / (10 ** 9)

        gpu_util, gpu_mem_gb = get_gpu_stats()

        data = {
            'cpu_util': cpu_util,
            'cpu_mem_gb': cpu_mem_gb,
            'gpu_util': gpu_util,
            'gpu_mem_gb': gpu_mem_gb,
        }
        print(json.dumps(data), flush=True)

        time.sleep(30)

if __name__ == '__main__':
    main()
