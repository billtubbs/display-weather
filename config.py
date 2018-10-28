#!/usr/bin/env python
"""-------------------- config.py --------------------
Loads private API key info from local file.

Typical usage:
>>> from config import load_from_config
>>> api_key = load_from_config('certain_api_key')
"""

import yaml
import logging

logging.basicConfig(
	filename='logfile.txt',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def load_from_config(key):

    with open("config.yaml", 'r') as f:
        try:
            params = yaml.load(f)
        except yaml.YAMLError as exc:
            logging.debug(exc)
        else:
            logging.info("Item retrieved from config file.")

    return params[key]
