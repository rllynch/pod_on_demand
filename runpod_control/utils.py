#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

import logging
from functools import cache
from types import SimpleNamespace

import runpod

logger = logging.getLogger(__name__)

@cache
def get_gpu_mem_gb(name):
    """
    Get the GPU memory size in GB for a given GPU name or ID.
    """
    logger.debug(f"Looking up GPU memory for: {name}")
    gpu_list = runpod.get_gpus()
    for gpu in gpu_list:
        if gpu['id'] == name or gpu['displayName'] == name:
            return gpu['memoryInGb']
    return None

def get_pod_info(name_or_pod):
    if isinstance(name_or_pod, str):
        pod_list = runpod.get_pods()
        pod_list = [pod for pod in pod_list if pod['name'] == name_or_pod]
        if len(pod_list) == 0:
            return None
        pod = pod_list[0]
    else:
        pod = name_or_pod

    return SimpleNamespace(
        name=pod['name'],
        id=pod['id'],
        cpu_mem_gb=pod['memoryInGb'],
        gpu_mem_gb=get_gpu_mem_gb(pod['machine']['gpuDisplayName']),
        is_running=pod['desiredStatus'] == 'RUNNING',
    )
