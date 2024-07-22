# -*- coding: utf-8 -*-
import click

from aiida.cmdline.params import options, arguments
from aiida.cmdline.utils import echo

from .root import cmd_root


@cmd_root.group("alloc")
def alloc_group():
    """Commands to configure HQ allocations."""


@alloc_group.command("add")
@click.argument("slurm-options", nargs=-1)
@options.COMPUTER(required=True)
@click.option(
    "-t",
    "--time-limit",
    type=str,
    required=True,
    help=(
        "Time limit for each job run by the allocation. The duration can be expressed using various shortcuts "
        "recognised by HyperQueue, e.g. 30m, 2h, ... For the full list, see https://tinyurl.com/hq-duration."
    ),
)
@click.option(
    "--hyper-threading/--no-hyper-threading",
    default=True,
    type=click.BOOL,
    help=("Allow HyperQueue to consider hyperthreads when assigning resources."),
)
@click.option(
    "-b",
    "--backlog",
    type=click.INT,
    required=False,
    default=1,
    help=(
        "Set the backlog for the allocator. This is the number of allocations HyperQueue will make sure is waiting with"
        " the job manager."
    ),
)
@click.option(
    "-w",
    "--workers-per-alloc",
    type=click.INT,
    required=False,
    default=1,
    help=("Option to allow pooled jobs to launch on multiple nodes."),
)
def cmd_add(
    slurm_options, computer, time_limit, hyper_threading, backlog, workers_per_alloc
):
    """Add a new allocation to the HQ server."""

    # from hq==0.13.0: ``--cpus=no-ht`` is now changed to a flag ``--no-hyper-threading``
    hyper = "" if hyper_threading else "--no-hyper-threading"

    with computer.get_transport() as transport:
        retval, _, stderr = transport.exec_command_wait(
            f'hq alloc add slurm --backlog {backlog} --time-limit {time_limit} --name ahq {hyper} '
            f'--workers-per-alloc {workers_per_alloc} -- {" ".join(slurm_options)}'
        )

    if retval != 0:
        echo.echo_critical(f"failed to create new allocation: {stderr}\n")

    echo.echo_success(f"{stderr}")


@alloc_group.command("list")
@arguments.COMPUTER()
def cmd_list(computer):
    """List the allocations on the HQ server."""

    with computer.get_transport() as transport:
        retval, stdout, stderr = transport.exec_command_wait("hq alloc list")

    if retval != 0:
        echo.echo_critical(f"failed to list allocations: {stderr}\n")

    echo.echo(stdout)


@alloc_group.command("remove")
@click.argument("alloc_id")
@options.COMPUTER(required=True)
def cmd_remove(alloc_id, computer):
    """Remove an allocation from the HQ server."""

    with computer.get_transport() as transport:
        retval, _, stderr = transport.exec_command_wait(f"hq alloc remove {alloc_id}")

    if retval != 0:
        echo.echo_critical(f"failed to remove allocation: {stderr}\n")

    echo.echo_success(f"{stderr}")
