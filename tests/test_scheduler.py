# -*- coding: utf-8 -*-
"""Tests for command line interface."""

import pytest
import uuid
from pathlib import Path

from aiida.schedulers import JobState
from aiida.common.datastructures import CodeRunMode
from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo
from aiida_hyperqueue.scheduler import HyperQueueJobResource, HyperQueueScheduler

from .conftest import HqEnv
from .utils import wait_for_job_state


@pytest.fixture
def valid_submit_script():
    scheduler = HyperQueueScheduler()

    job_tmpl = JobTemplate()
    job_tmpl.job_name = "echo hello"
    job_tmpl.shebang = "#!/bin/bash"
    job_tmpl.uuid = str(uuid.uuid4())
    job_tmpl.job_resource = scheduler.create_job_resource(num_cpus=1)
    job_tmpl.max_wallclock_seconds = 24 * 3600
    tmpl_code_info = JobTemplateCodeInfo()
    tmpl_code_info.cmdline_params = ["echo", "Hello"]
    job_tmpl.codes_info = [tmpl_code_info]
    job_tmpl.codes_run_mode = CodeRunMode.SERIAL

    return scheduler.get_submit_script(job_tmpl)


def test_resource_validation():
    """Tests to verify that resources are correctly validated."""
    resource = HyperQueueJobResource(num_cpus=16, memory_mb=20)
    assert resource.num_cpus == 16
    assert resource.memory_mb == 20

    # If memory_mb not set, the default value 0 will be assigned
    resource = HyperQueueJobResource(num_cpus=16)
    assert resource.num_cpus == 16
    assert resource.memory_mb is None

    # raise if num_cpus is not set
    with pytest.raises(
        KeyError,
        match="Must specify `num_cpus`",
    ):
        HyperQueueJobResource()

    # raise if num_cpus is not integer
    with pytest.raises(
        ValueError,
        match="`num_cpus` must be an integer",
    ):
        HyperQueueJobResource(num_cpus=1.2)

    # raise if memory_mb is not integer
    with pytest.raises(
        ValueError,
        match="`memory_mb` must be an integer",
    ):
        HyperQueueJobResource(num_cpus=4, memory_mb=1.2)


def test_submit_command():
    """Test submit command"""
    scheduler = HyperQueueScheduler()

    assert "hq submit --output-mode=json job.sh" == scheduler._get_submit_command(
        "job.sh"
    )


def test_parse_submit_command_output(hq_env: HqEnv, valid_submit_script):
    """Test parsing the output of submit command"""
    hq_env.start_server()
    hq_env.start_worker(cpus="1")
    Path("_aiidasubmit.sh").write_text(valid_submit_script)

    scheduler = HyperQueueScheduler()
    args = scheduler._get_submit_command("_aiidasubmit.sh")
    args = args.split(" ")[1:]
    process = hq_env.command(
        args,
        wait=False,
        ignore_stderr=True,
    )
    stdout = process.communicate()[0].decode()
    stderr = ""
    retval = process.returncode

    assert retval == 0

    scheduler = HyperQueueScheduler()
    job_id = scheduler._parse_submit_output(retval, stdout, stderr)

    assert job_id == "1"


def test_submit_script():
    """Test the creation of a simple submission script."""
    VALID_SCRIPT_CONTENT = """#!/bin/bash
#HQ --time-request=86400s
#HQ --time-limit=86400s
#HQ --cpus=2
#HQ --resource mem=256

'mpirun' '-np' '4' 'pw.x' '-npool' '1' < 'aiida.in'
"""

    scheduler = HyperQueueScheduler()

    job_tmpl = JobTemplate()
    job_tmpl.shebang = "#!/bin/bash"
    job_tmpl.uuid = str(uuid.uuid4())
    job_tmpl.job_resource = scheduler.create_job_resource(num_cpus=2, memory_mb=256)
    job_tmpl.max_wallclock_seconds = 24 * 3600
    tmpl_code_info = JobTemplateCodeInfo()
    tmpl_code_info.cmdline_params = ["mpirun", "-np", "4", "pw.x", "-npool", "1"]
    tmpl_code_info.stdin_name = "aiida.in"
    job_tmpl.codes_info = [tmpl_code_info]
    job_tmpl.codes_run_mode = CodeRunMode.SERIAL

    submit_script_text = scheduler.get_submit_script(job_tmpl)

    assert submit_script_text == VALID_SCRIPT_CONTENT


def test_submit_script_mem_not_specified():
    """Test if memory_mb not pass to resource, it will not specified in job script"""
    scheduler = HyperQueueScheduler()

    job_tmpl = JobTemplate()
    job_tmpl.shebang = "#!/bin/bash"
    job_tmpl.uuid = str(uuid.uuid4())
    job_tmpl.job_resource = scheduler.create_job_resource(num_cpus=2)
    job_tmpl.max_wallclock_seconds = 24 * 3600
    tmpl_code_info = JobTemplateCodeInfo()
    tmpl_code_info.cmdline_params = ["mpirun", "-np", "4", "pw.x", "-npool", "1"]
    tmpl_code_info.stdin_name = "aiida.in"
    job_tmpl.codes_info = [tmpl_code_info]
    job_tmpl.codes_run_mode = CodeRunMode.SERIAL

    submit_script_text = scheduler.get_submit_script(job_tmpl)

    assert "#HQ --resource mem" not in submit_script_text


def test_submit_script_is_hq_valid(hq_env: HqEnv, valid_submit_script):
    """The generated script can actually be run by hq"""
    hq_env.start_server()
    hq_env.start_worker(cpus="1")
    Path("_aiidasubmit.sh").write_text(valid_submit_script)
    hq_env.command(["submit", "_aiidasubmit.sh"])
    table = hq_env.command(["job", "info", "1"], as_table=True)

    assert table.get_row_value("Name") == "echo hello"
    assert "cpus: 1 compact" in table.get_row_value("Resources")

    wait_for_job_state(hq_env, 1, "FINISHED")

    assert table.get_row_value("State") == "FINISHED"


def test_get_and_parse_joblist(hq_env: HqEnv):
    """Test whether _parse_joblist_output can parse the hq job list output"""
    scheduler = HyperQueueScheduler()

    joblist_command = scheduler._get_joblist_command().split(" ")[1:]

    hq_env.start_server()

    # waiting and cancel
    hq_env.command(["submit", "--", "bash", "-c", "echo '1 canceled'"])
    hq_env.command(["submit", "--", "bash", "-c", "echo '2 waiting'"])
    hq_env.command(
        ["submit", "--", "bash", "-c", "echoooo '3 failed'"]
    )  # This job will failed

    r = hq_env.command(["job", "cancel", "1"])
    assert "Job 1 canceled" in r

    joblist: str = hq_env.command(joblist_command)

    # Test parse waiting
    job_info_list = scheduler._parse_joblist_output(0, joblist, "")

    assert len(job_info_list) == 2

    for job_info in job_info_list:
        assert job_info.title == "bash"
        assert job_info.job_state == JobState.QUEUED

    ## Let job 2, 3 finished, thus disappeared from job list output
    hq_env.start_worker(cpus=1)

    wait_for_job_state(hq_env, 2, "FINISHED")
    wait_for_job_state(hq_env, 3, "FAILED")

    # Test parse running
    hq_env.command(["submit", "--", "sleep", "1"])

    wait_for_job_state(hq_env, 4, "RUNNING")

    joblist: str = hq_env.command(joblist_command)

    # Test parse waiting
    job_info_list = scheduler._parse_joblist_output(0, joblist, "")

    assert len(job_info_list) == 1
    assert job_info_list[0].job_state == JobState.RUNNING
    assert job_info_list[0].title == "sleep"
