#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

from pathlib import Path
from functools import cache
from pprint import pprint

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import runpod

script_dir = Path(__file__).parent

@cache
def get_secrets():
    '''Load secrets from a YAML file.'''
    with open(script_dir / 'secrets.yaml') as stream:
        data = load(stream, Loader=Loader)
    return data

@cache
def get_secret(name):
    '''Get a secret value by name.'''
    try:
        return get_secrets()[name]
    except KeyError as ex:
        raise KeyError(f"Secret '{name}' not found in secrets.yaml") from ex

def secret_constructor(loader, node):
    '''Handle !secret tags in YAML to retrieve secrets from secrets.yaml.'''
    value = loader.construct_scalar(node)
    return get_secret(value)

def file_constructor(loader, node):
    '''Handle !file tags in YAML to read file contents.'''
    value = loader.construct_scalar(node)
    value = Path(value).expanduser()
    with open(value) as file:
        return file.read().strip()

@cache
def get_config():
    '''Get complete configuration from config.yaml.'''
    Loader.add_constructor('!secret', secret_constructor)
    Loader.add_constructor('!file', file_constructor)

    with open(script_dir / 'config.yaml') as stream:
        data = load(stream, Loader=Loader)
    return data

def setup_runpod():
    runpod.api_key = get_config()['runpod']['api_key']

if __name__ == "__main__":
    # Debug - print the configuration
    pprint(get_config())
