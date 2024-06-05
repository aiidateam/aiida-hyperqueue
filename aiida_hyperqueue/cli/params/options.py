# -*- coding: utf-8 -*-
"""Reusable options for CLI commands."""

import functools

import click
from aiida.cmdline.params import options as core_options
from aiida.cmdline.params import types as core_types

__all__ = (
    "PROFILE",
    "VERBOSITY",
    "VERSION",
)

PROFILE = functools.partial(
    core_options.PROFILE,
    type=core_types.ProfileParamType(load_profile=True),
    expose_value=False,
)

# Clone the ``VERBOSITY`` option from ``aiida-core`` so the ``-v`` short flag can be removed, since that overlaps with
# the flag of the ``VERSION`` option of this CLI.
VERBOSITY = core_options.VERBOSITY.clone()
VERBOSITY.args = ("--verbosity",)

VERSION = core_options.OverridableOption(
    "-v",
    "--version",
    type=click.STRING,
    required=False,
    help="Select the version of the installed configuration.",
)
