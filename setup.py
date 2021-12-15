# -*- coding: utf-8 -*-
"""Setup script for aiida-hyperqueue"""
import json
from pathlib import Path
from setuptools import setup, find_packages

with Path('README.md').open('r', encoding='utf8') as handle:
    LONG_DESCRIPTION = handle.read()

if __name__ == '__main__':
    # Provide static information in setup.json
    # such that it can be discovered automatically
    with Path('setup.json').open('r', encoding='utf8') as info:
        kwargs = json.load(info)
    setup(
        packages=find_packages(
            include=['aiida_hyperqueue', 'aiida_hyperqueue.*']),
        # this doesn't work when placed in setup.json (something to do with str type)
        package_data={
            '': ['*'],
        },
        long_description=LONG_DESCRIPTION,
        long_description_content_type='text/markdown',
        **kwargs)
