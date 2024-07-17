# -*- coding: utf-8 -*-
import pytest
from click.testing import CliRunner

from aiida.transports.transport import Transport as TransportClass


@pytest.fixture
def runner():
    return CliRunner()


original_exec_command_wait = TransportClass.exec_command_wait

# TODO: Not yet implemented, seems hard to just use hq_env
# If using real command, I need to handle the grace for teardown of tests
