import pytest
from aiida_hyperqueue.cli import cmd_install
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


def test_install(runner, tmp_path, aiida_computer_local):
    aiida_computer_local(label="localhost-hq")

    version = "0.19.0"
    result = runner.invoke(
        cmd_install,
        [
            "-p",
            f"{tmp_path.resolve()!s}",
            "--hq-version",
            version,
            "--no-write-bashrc",
            "localhost-hq",
        ],
    )

    assert result.exit_code == 0
    assert f"hq version {version}" in result.output
