# -*- coding: utf-8 -*-
import pytest
import time
from click.testing import CliRunner

from aiida.transports.transport import Transport as TransportClass
from aiida_hyperqueue.cli import cmd_info, cmd_start, cmd_stop

from .conftest import HqEnv, get_hq_binary


@pytest.fixture
def runner():
    return CliRunner()


original_exec_command_wait = TransportClass.exec_command_wait


@pytest.fixture
def hq_env_mock_exec_command_wait(hq_env: HqEnv):
    def _mock_exec_command_wait(obj, command: str, **kwargs):
        """mock `exec_command_wait` method of Transport Abstract class.
        Since it is an object method, its first parameter is self.

        This function is for running the `hq` command through the temperory hq_env
        fixture.
        If the command start with "hq" we regard it running the hq command and pass it
        to the hq_env to run, otherwith use the original behavior.
        """
        if command.startswith("hq"):
            process = hq_env.command(
                command.split(" ")[1:], wait=False, ignore_stderr=True
            )

            stdout = process.communicate()[0].decode()
            stderr = ""
            retval = process.returncode
        else:
            retval, stdout, stderr = original_exec_command_wait(obj, command, **kwargs)

        return retval, stdout, stderr

    return _mock_exec_command_wait


@pytest.fixture
def server_dir_mock_exec_command_wait(tmp_path):
    def _mock_exec_command_wait(obj, command: str, **kwargs):
        """mock `exec_command_wait` method of Transport Abstract class.
        Since it is an object method, its first parameter is self.

        Different from `hq_env_mock_exec_command_wait` this one run with changing the server_dir
        and did not handle the clean up of stop the hq.
        """
        hq = get_hq_binary()
        cmd_list = command.split(" ")
        if command.startswith("hq"):  # `hq`
            command = " ".join(
                [f"{hq}", "--server-dir", f"{str(tmp_path.resolve())}"] + cmd_list[1:]
            )
        elif command.startswith("nohup hq"):  # `nohup hq`
            command = " ".join(
                [f"nohup {hq}", "--server-dir", f"{str(tmp_path.resolve())}"]
                + cmd_list[2:]
            )

        retval, stdout, stderr = original_exec_command_wait(obj, command, **kwargs)

        return retval, stdout, stderr

    return _mock_exec_command_wait


def test_server_info_direct(
    runner: CliRunner,
    aiida_computer_local,
    monkeypatch: pytest.MonkeyPatch,
    hq_env_mock_exec_command_wait,
    hq_env: HqEnv,
):
    """Test server info, test against local transport"""
    aiida_computer_local(label="localhost")

    monkeypatch.setattr(
        TransportClass, "exec_command_wait", hq_env_mock_exec_command_wait
    )

    result = runner.invoke(cmd_info, "localhost")
    assert result.exit_code == 1
    assert "Critical: cannot obtain HyperQueue server information" in result.output

    hq_env.start_server()
    result = runner.invoke(cmd_info, "localhost")

    assert result.exit_code == 0
    assert "Start date" in result.output


def test_server_start_info_stop_circle(
    runner: CliRunner,
    aiida_computer_local,
    monkeypatch: pytest.MonkeyPatch,
    hq_env_mock_exec_command_wait,
    server_dir_mock_exec_command_wait,
    tmp_path,
):
    """Test server start, info, stop cile

    NOTE: this test is run hq command using the system process instead of using the hq_env which handle the drop operation
    to clean the files and process.
    Therefor, it may cause problem that the process are left not cleaned.
    """
    aiida_computer_local(label="localhost-hq")

    monkeypatch.setattr(
        TransportClass, "exec_command_wait", server_dir_mock_exec_command_wait
    )

    # Before start, server info will fail
    result = runner.invoke(cmd_info, "localhost-hq")

    assert result.exit_code == 1
    assert "Critical: cannot obtain HyperQueue server information" in result.output

    # Start server
    result = runner.invoke(cmd_start, "localhost-hq")

    assert result.exit_code == 0

    # Wait a bit until the server is start
    time.sleep(2)

    # Check the hq server is started
    result = runner.invoke(cmd_info, "localhost-hq")

    assert result.exit_code == 0
    assert "Start date" in result.output

    # If I start again -> "server is already running"
    result = runner.invoke(cmd_start, "localhost-hq")

    # Stop the hq server
    result = runner.invoke(cmd_stop, "localhost-hq")

    assert result.exit_code == 0

    # Check info again
    result = runner.invoke(cmd_info, "localhost-hq")

    assert result.exit_code == 1
    assert "Critical: cannot obtain HyperQueue server information" in result.output
