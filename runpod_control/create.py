#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

import os
import logging

import runpod

from config import get_config, setup_runpod

logger = logging.getLogger(__name__)

def create_pod():
    logger.info("Creating pod...")

    kwargs = get_config()['runpod']['pod']
    logger.debug(f'Pod configuration: {kwargs}')

    new_pod = runpod.create_pod(**kwargs)
    logger.info(f'New pod: {new_pod}')

    return new_pod

def main():
    logging.basicConfig(level=logging.INFO)
    setup_runpod()

    pod_list = runpod.get_pods()
    assert len(pod_list) == 0, "There are already pods running. Please stop them before creating a new one."

    new_pod = create_pod()

if __name__ == "__main__":
    main()
