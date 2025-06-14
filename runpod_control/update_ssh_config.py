#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

import subprocess
import logging
import re
import time
import asyncio
from pathlib import Path

import runpod

from config import get_config, setup_runpod

logger = logging.getLogger(__name__)

def get_ssh_ip_port():
    name = get_config()['runpod']['pod']['name']
    pod_list = runpod.get_pods()
    pod_list = [pod for pod in pod_list if pod['name'] == name]
    if len(pod_list) != 1:
        return None, None
    if not pod_list[0]['runtime']:
        return None, None
    if 'ports' not in pod_list[0]['runtime']:
        return None, None
    if not pod_list[0]['runtime']['ports']:
        return None, None

    ssh_port = [port for port in pod_list[0]['runtime']['ports'] if port['privatePort'] == 22]
    assert len(ssh_port) == 1

    ssh_port = ssh_port[0]
    return ssh_port['ip'], ssh_port['publicPort']

async def update_ssh_config(wait=True, replace=True, prompt_replace=True):
    target_hostname = get_config()['runpod']['pod']['name']

    ssh_ip, ssh_port = get_ssh_ip_port()
    if wait:
        if not ssh_ip or not ssh_port:
            logger.info("Waiting for SSH IP and port to be available...")
        while not ssh_ip or not ssh_port:
            await asyncio.sleep(5)
            ssh_ip, ssh_port = get_ssh_ip_port()
    else:
        raise ConnectionError("SSH IP or port not found. Please ensure the pod is running and SSH is enabled.")

    orig_fn = Path.home() / '.ssh' / 'config'
    new_fn = Path.home() / '.ssh' / 'config.new'
    old_fn = Path.home() / '.ssh' / 'config.old'

    current_host = None
    hostname_re = re.compile(r'HostName \S+')
    port_re = re.compile(r'Port \d+')

    with open(orig_fn) as input_file, open(new_fn, 'w') as output_file:
        for line in input_file.readlines():
            tokens = line.strip().split()
            if len(tokens) > 1 and tokens[0] == 'Host':
                current_host = tokens[1]

            if current_host == target_hostname:
                line = re.sub(hostname_re, f'HostName {ssh_ip}', line)
                line = re.sub(port_re, f'Port {ssh_port}', line)

            output_file.write(line)

    subprocess.run(['diff', orig_fn, new_fn], check=False)

    with open(orig_fn) as orig_file, open(new_fn) as new_file:
        orig_content = orig_file.read()
        new_content = new_file.read()
        if orig_content == new_content:
            logger.info("SSH config is already up to date.")
            return

    if replace and prompt_replace:
        # Get confirmation from user before overwriting the original config
        confirm = input("Do you want to overwrite the original SSH config file? (y/n): ").strip().lower()
        if confirm not in ('y', 'yes'):
            replace = False
    if replace:
        old_fn.unlink(missing_ok=True)
        orig_fn.rename(old_fn)
        new_fn.rename(orig_fn)

    logger.info(f'SSH config updated for {target_hostname} to {ssh_ip}:{ssh_port}')

async def main():
    logging.basicConfig(level=logging.INFO)
    setup_runpod()

    await update_ssh_config()

if __name__ == "__main__":
    asyncio.run(main())
