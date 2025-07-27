#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

import os
import logging

import runpod

from config import get_config, setup_runpod

logger = logging.getLogger(__name__)

SCRIPT_ORDER = (
    (None,           'setup_os.sh'),
    (None,           'setup_venv.sh'),
    ('huggingface',  'setup_huggingface.sh'),
    ('comfyui',      'setup_comfyui.sh'),
    ('comfyui',      'setup_comfyui_models.sh'),
    ('ollama',       'setup_ollama.sh'),
    ('ollama',       'run_ollama.sh'),
    ('ollama',       'setup_ollama_models.sh'),
    ('comfyui',      'run_comfyui.sh'), # ComfyUI may depend on the ollama Python package so run it after setting up Ollama
    ('kohya_ss',     'setup_kohya_ss.sh'),
    ('kohya_ss',     'run_kohya_ss.sh'),
    (None,           'report_disk_usage.sh'),
)

def create_pod():
    logger.info("Creating pod...")
    config = get_config()

    kwargs = config['runpod']['pod']
    kwargs['env']['MODELS'] = ':'.join(config['runpod']['models'])
    setup_scripts = [fn for module, fn in SCRIPT_ORDER if module is None or module in config['runpod']['modules']]
    kwargs['env']['SETUP_SCRIPTS'] = ' '.join(setup_scripts)
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
