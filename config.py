#!/usr/bin/env python
"""-------------------- config.py --------------------
Loads private API key info from local file.

Typical usage:
>>> from config import load_from_config
>>> api_key = load_from_config('certain_api_key')
"""

import yaml

def load_from_config(key):

    with open("config.yaml", 'r') as f:
        try:
            params = yaml.load(f)
        except yaml.YAMLError as exc:
            print(exc)

    return params[key]
