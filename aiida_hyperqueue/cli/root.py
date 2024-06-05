# -*- coding: utf-8 -*-
"""Command line interface `aiida-hq` for aiida-hyperqueue.
The CLI implementation prototype from `aiida-pseudo`.
"""

import click

from aiida.cmdline.groups.verdi import VerdiCommandGroup

from .params import options


class CustomVerdiCommandGroup(VerdiCommandGroup):
    """Subclass of :class:`aiida.cmdline.groups.verdi.VerdiCommandGroup` for the CLI.

    This subclass overrides the verbosity option to use a custom one that removes the ``-v`` short version of the option
    since that is used by other options in this CLI and so would clash.
    """

    @staticmethod
    def add_verbosity_option(cmd):
        """Apply the ``verbosity`` option to the command, which is common to all subcommands."""
        if cmd is not None and "verbosity" not in [param.name for param in cmd.params]:
            cmd = options.VERBOSITY()(cmd)

        return cmd


@click.group(
    "aiida-hq",
    cls=CustomVerdiCommandGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@options.VERBOSITY()
@options.PROFILE()
def cmd_root():
    """CLI for the ``aiida-hyperqueue`` plugin."""
