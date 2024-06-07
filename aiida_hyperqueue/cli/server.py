# -*- coding: utf-8 -*-
import click

from aiida.cmdline.utils import echo

from .root import cmd_root
from .params import arguments


@cmd_root.group("server")
def server_group():
    """Commands for interacting with the HQ server."""


@server_group.command("start")
@arguments.COMPUTER()
@click.option(
    "-d",
    "--domain",
    required=False,
    type=click.STRING,
    help="domain that will attached to the `hostname` of remote.",
)
def cmd_start(computer, domain: str):
    """Start the HyperQueue server."""

    with computer.get_transport() as transport:
        retval, _, _ = transport.exec_command_wait("hq server info")

    if retval == 0:
        echo.echo_info("server is already running!")
        return

    with computer.get_transport() as transport:
        # Mostly the case needed by CSCS machines
        # The hostname has not domain included, it requires with domain to connect login node from compute node
        # We attach the domain name to the hostname manually and passed to the start command.

        # start command
        start_command_lst = ["nohup", "hq", "server", "start"]

        if domain is not None:
            retval, stdout, stderr = transport.exec_command_wait("hostname")
            if retval != 0:
                echo.echo_critical(f"unable to get the hostname: {stderr}")
            else:
                hostname = stdout.strip()
                start_command_lst.extend(["--host", f"{hostname}.{domain}"])

        start_command_lst.extend(
            [
                "1>$HOME/.hq-stdout",
                "2>$HOME/.hq-stderr",
                "&",
            ]
        )
        start_command = " ".join(start_command_lst)

        echo.echo_debug(f"Run start command {start_command} on the remote")

        # It requires to sleep a bit after the nohup see https://github.com/aiidateam/aiida-core/issues/6377
        # This setup require aiida-core >= 2.5.2
        retval, stdout, stderr = transport.exec_command_wait(
            start_command,
            timeout=0.1,
        )

        if retval != 0:
            echo.echo_critical(f"unable to start the server: {stderr}")

    echo.echo_success("HQ server started!")


@server_group.command("stop")
@arguments.COMPUTER()
def cmd_stop(computer):
    """Start the HyperQueue server."""

    with computer.get_transport() as transport:
        retval, _, _ = transport.exec_command_wait("hq server info")

    if retval != 0:
        echo.echo_info("server is not running!")
        return

    echo.echo_info("Stop the hq server will close all allocs.")

    with computer.get_transport() as transport:
        retval, _, stderr = transport.exec_command_wait("hq server stop")

    if retval != 0:
        echo.echo_critical(f"unable to stop the server: {stderr}")

    echo.echo_success("HQ server stopped!")


@server_group.command("restart")
@arguments.COMPUTER()
# TODO: how to pass domain to restart???
@click.pass_context
def cmd_restart(ctx, computer):
    """Restart the HyperQueue server by stop and start again"""
    ctx.forward(cmd_stop)
    ctx.forward(cmd_start)


@server_group.command("info")
@arguments.COMPUTER()
def cmd_info(computer):
    """Get information on the HyperQueue server."""

    with computer.get_transport() as transport:
        retval, stdout, stderr = transport.exec_command_wait("hq server info")

    if retval != 0:
        echo.echo_critical(
            f"cannot obtain HyperQueue server information: {stderr}\n"
            "Try starting the server with `aiida-qe server start`."
        )

    echo.echo(stdout)
