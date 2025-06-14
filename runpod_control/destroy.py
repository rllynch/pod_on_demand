#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

import os
import logging

import runpod

from config import get_config, setup_runpod

logger = logging.getLogger(__name__)

def terminate_pod():
    name = get_config()['runpod']['pod']['name']

    pod_list = runpod.get_pods()
    pod_list = [pod for pod in pod_list if pod['name'] == name]
    assert len(pod_list) == 1

    pod = pod_list[0]
    logger.info(f'Terminating pod: {pod}')

    runpod.terminate_pod(pod['id'])

def main():
    logging.basicConfig(level=logging.INFO)
    setup_runpod()

    terminate_pod()

if __name__ == "__main__":
    main()
