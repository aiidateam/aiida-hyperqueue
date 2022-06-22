# -*- coding: utf-8 -*-
"""Command line interface (CLI) for aiida_hyperqueue."""

import click
from aiida.cmdline.params import options, arguments
from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.commands.cmd_data import verdi_data


@verdi_data.group('hyperqueue')
def data_cli():
    """Command line interface for aiida-hyperqueue"""


@data_cli.group('server')
def server_group():
    """Commands for interacting with the HQ server."""


@server_group.command('start')
@arguments.COMPUTER()
@decorators.with_dbenv()
def start_cmd(computer):
    """Start the HyperQueue server."""

    with computer.get_transport() as transport:
        retval, _, _ = transport.exec_command_wait('hq server info')

    if retval == 0:
        echo.echo_info('server is already running!')
        return

    with computer.get_transport() as transport:
        retval, _, stderr = transport.exec_command_wait(
            'nohup hq server start 1>$HOME/.hq-stdout 2>$HOME/.hq-stderr &')

    if retval != 0:
        echo.echo_critical(f'unable to start the server: {stderr}')

    echo.echo_success('HQ server started!')


@server_group.command('info')
@arguments.COMPUTER()
@decorators.with_dbenv()
def info_cmd(computer):
    """Get information on the HyperQueue server."""

    with computer.get_transport() as transport:
        retval, stdout, stderr = transport.exec_command_wait('hq server info')

    if retval != 0:
        echo.echo_critical(
            f'cannot obtain HyperQueue server information: {stderr}\n'
            'Try starting the server with `verdi data hyperqueue server start`.'
        )

    echo.echo(stdout)


@data_cli.group('alloc')
def alloc_group():
    """Commands to configure HQ allocations."""


@alloc_group.command('add')
@click.argument('slurm-options', nargs=-1)
@options.COMPUTER(required=True)
@click.option(
    '-t',
    '--time-limit',
    type=str,
    required=True,
    help=
    ('Time limit for each job run by the allocation. The duration can be expressed using various shortcuts '
     'recognised by HyperQueue, e.g. 30m, 2h, ... For the full list, see https://tinyurl.com/hq-duration.'
     ))
@click.option(
    '-H',
    '--enable-hyperthreading',
    type=click.BOOL,
    is_flag=True,
    help=(
        'Allow HyperQueue to consider hyperthreads when assigning resources.'))
@click.option(
    '-b',
    '--backlog',
    type=click.INT,
    required=False,
    default=0,
    help=(
        'Allow HyperQueue to consider hyperthreads when assigning resources.'))
@click.option(
    '-w',
    '--workers-per-alloc',
    type=click.INT,
    required=False,
    default=1,
    help=(
        'Option to allow pooled jobs to launch on multiple nodes.'))

@decorators.with_dbenv()
def add_cmd(slurm_options, computer, time_limit,  enable_hyperthreading, backlog, workers_per_alloc):
    """Add a new allocation to the HQ server."""

    hyper = '' if enable_hyperthreading else '--cpus no-ht'

    with computer.get_transport() as transport:
        retval, _, stderr = transport.exec_command_wait(
            f'hq alloc add slurm --backlog {backlog} --time-limit {time_limit} --name aiida {hyper} --workers-per-alloc {workers_per_alloc} -- {" ".join(slurm_options)}'
        )

    if retval != 0:
        echo.echo_critical(f'failed to create new allocation: {stderr}\n')

    echo.echo_success(f'{stderr}')


@alloc_group.command('list')
@arguments.COMPUTER()
@decorators.with_dbenv()
def list_cmd(computer):
    """List the allocations on the HQ server."""

    with computer.get_transport() as transport:
        retval, stdout, stderr = transport.exec_command_wait('hq alloc list')

    if retval != 0:
        echo.echo_critical(f'failed to list allocations: {stderr}\n')

    echo.echo(stdout)


@alloc_group.command('remove')
@click.argument('alloc_id')
@options.COMPUTER(required=True)
@decorators.with_dbenv()
def remove_cmd(alloc_id, computer):
    """Remove an allocation from the HQ server."""

    with computer.get_transport() as transport:
        retval, _, stderr = transport.exec_command_wait(
            f'hq alloc remove {alloc_id}')

    if retval != 0:
        echo.echo_critical(f'failed to remove allocation: {stderr}\n')

    echo.echo_success(f'{stderr}')
