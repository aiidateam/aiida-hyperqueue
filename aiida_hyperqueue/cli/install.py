# -*- coding: utf-8 -*-
import click
import tempfile
import requests
import tarfile
from pathlib import Path

from aiida import orm
from aiida.cmdline.utils import echo

from .params import arguments
from .root import cmd_root


@cmd_root.command("install")
@arguments.COMPUTER()
@click.option(
    "-p",
    "--remote-bin-dir",
    type=click.Path(),
    default=Path("$HOME/bin/"),
    help="remote bin path hq will stored.",
)
@click.option(
    "--write-bashrc/--no-write-bashrc",
    default=True,
    help="write the bin path to bashrc.",
)
@click.option(
    "--hq-version", type=str, default="0.19.0", help="the hq version will be installed."
)
# TODO: should also support different arch binary??
def cmd_install(
    computer: orm.Computer, remote_bin_dir: Path, hq_version: str, write_bashrc: bool
):
    """Install the hq binary to the computer through the transport"""

    # The minimal hq version we support is 0.13.0, check the minor version
    try:
        _, minor, _ = hq_version.split(".")
    except ValueError as e:
        echo.echo_critical(f"Cannot parse the version {hq_version}: {e}")
    else:
        if int(minor) < 13:
            # `--no-hyper-threading` replace `--cpus=no-ht` from 0.13.0
            # If older version installed, try to not use `--no-hyper-threading` for `aiida-hq alloc add`.
            echo.echo_warning(
                f"You are installing hq version {hq_version}, please do not use `--no-hyper-threading` for `aiida-hq alloc add`."
                " Or install version >= 0.13.0"
            )

    # Download the hq binary with specific version to local temp folder
    # raise if the version not found
    # Then upload to the remote using opened transport of computer
    with tempfile.TemporaryDirectory() as temp_dir:
        url = f"https://github.com/It4innovations/hyperqueue/releases/download/v{hq_version}/hq-v{hq_version}-linux-x64.tar.gz"
        response = requests.get(url, stream=True)
        rcode = response.status_code

        if rcode != 200:
            echo.echo_error(
                "Cannot download the hq, please check the version is exist."
            )

        temp_dir = Path(temp_dir)
        tar_path = temp_dir / "hq.tar.gz"

        with open(tar_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        with tarfile.open(tar_path, "r") as tar:
            tar.extractall(path=temp_dir)

        echo.echo_success(f"The hq version {hq_version} binary downloaded.")

        bin_path = temp_dir / "hq"

        # upload the binary to remote
        # TODO: try not override if the binary exist, put has overwrite=True as default
        with computer.get_transport() as transport:
            # Get the abs path of remote bin dir
            retval, stdout, stderr = transport.exec_command_wait(
                f"echo {str(remote_bin_dir)}"
            )
            if retval != 0:
                echo.echo_critical(
                    f"Not able to parse remote bin dir {remote_bin_dir}, exit_code={retval}"
                )
            else:
                remote_bin_dir = Path(stdout.strip())

            # first check if the hq exist in the target folder
            if transport.isfile(str(remote_bin_dir / "hq")):
                echo.echo_info(
                    f"hq exist in the {remote_bin_dir} on remote, will override it."
                )

            transport.makedirs(path=remote_bin_dir, ignore_existing=True)
            transport.put(
                localpath=str(bin_path.resolve()), remotepath=str(remote_bin_dir)
            )

            # XXX: should transport.put take care of this already??
            transport.exec_command_wait(f"chmod +x {str(remote_bin_dir / 'hq')}")

            # write to bashrc
            if write_bashrc:
                identity_str = "by aiida-hq"
                retval, _, stderr = transport.exec_command_wait(
                    f"grep -q '# {identity_str}' ~/.bashrc || echo '# {identity_str}\nexport PATH=$HOME/bin:$PATH' >> ~/.bashrc"
                )

                if retval != 0:
                    echo.echo_critical(
                        f"Not able to set set the path $HOME/bin to your remote bashrc, try to do it manually.\n"
                        f"Info: {stderr}"
                    )

    echo.echo_success(f"The hq binary installed into remote {remote_bin_dir}")
