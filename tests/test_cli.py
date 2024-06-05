import pytest
from click.testing import CliRunner

from aiida.transports.transport import Transport as TransportClass
from aiida_hyperqueue.cli import cmd_info

from .conftest import HqEnv

@pytest.fixture
def runner():
    return CliRunner()

original_exec_command_wait = TransportClass.exec_command_wait

@pytest.fixture
def mock_exec_command_wait(hq_env: HqEnv):
    
    def _mock_exec_command_wait(obj, command: str, **kwargs):
        """mock `exec_command_wait` method of Transport Abstract class.
        Since it is an object method, its first parameter is self.
        
        This function is for running the `hq` command through the temperory hq_env
        fixture.
        If the command start with "hq" we regard it running the hq command and pass it
        to the hq_env to run, otherwith use the original behavior.
        """
        if command.startswith("hq"):
            process = hq_env.command(command.split(' ')[1:], wait=False, ignore_stderr=True)

            stdout = process.communicate()[0].decode()
            stderr = ""
            retval = process.returncode
        else:
            retval, stdout, stderr = original_exec_command_wait(obj, command, **kwargs)
    
        return retval, stdout, stderr

    return _mock_exec_command_wait

def test_server_info(runner: CliRunner, aiida_computer_ssh, monkeypatch: pytest.MonkeyPatch, mock_exec_command_wait, hq_env: HqEnv):
    """Test server info"""
    aiida_computer_ssh(label='localhost-hq')

    monkeypatch.setattr(TransportClass, "exec_command_wait", mock_exec_command_wait)

    hq_env.start_server()
    result = runner.invoke(cmd_info, "localhost-hq")

    print(result)
    print(result.output)

