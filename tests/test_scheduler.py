# -*- coding: utf-8 -*-
"""Tests for command line interface."""
import pytest
import datetime
import logging
import unittest
import uuid
from pathlib import Path

from aiida.engine import CalcJob
from aiida.schedulers import JobState, SchedulerError
from aiida.common.datastructures import CodeRunMode
from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo
from aiida_hyperqueue.scheduler import HyperQueueJobResource, HyperQueueScheduler

from .conftest import HqEnv
from .utils import wait_for_job_state

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
        match='Must specify `num_cpus`',
    ):
        HyperQueueJobResource()

    # raise if num_cpus is not integer
    with pytest.raises(
        ValueError,
        match='`num_cpus` must be an integer',
    ):
        HyperQueueJobResource(num_cpus=1.2)

    # raise if memory_mb is not integer
    with pytest.raises(
        ValueError,
        match='`memory_mb` must be an integer',
    ):
        HyperQueueJobResource(num_cpus=4, memory_mb=1.2)


#def test_parse_common_joblist_output():
#    """Test whether _parse_joblist_output can parse the squeue output"""
#    scheduler = SlurmScheduler()
#
#    retval = 0
#    stdout = TEXT_SQUEUE_TO_TEST
#    stderr = ''
#
#    job_list = scheduler._parse_joblist_output(retval, stdout, stderr)
#    job_dict = {j.job_id: j for j in job_list}
#
#    # The parameters are hard coded in the text to parse
#    job_parsed = len(job_list)
#    assert job_parsed == JOBS_ON_CLUSTER
#
#    job_running_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.RUNNING])
#    assert len(JOBS_RUNNING) == job_running_parsed
#
#    job_held_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.QUEUED_HELD])
#    assert JOBS_HELD == job_held_parsed
#
#    job_queued_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.QUEUED])
#    assert JOBS_QUEUED == job_queued_parsed
#
#    parsed_running_users = [j.job_owner for j in job_list if j.job_state and j.job_state == JobState.RUNNING]
#    assert set(USERS_RUNNING) == set(parsed_running_users)
#
#    parsed_running_jobs = [j.job_id for j in job_list if j.job_state and j.job_state == JobState.RUNNING]
#    assert set(JOBS_RUNNING) == set(parsed_running_jobs)
#
#    assert job_dict['863553'].requested_wallclock_time_seconds, 30 * 60
#    assert job_dict['863553'].wallclock_time_seconds, 29 * 60 + 29
#    assert job_dict['863553'].dispatch_time, datetime.datetime(2013, 5, 23, 11, 44, 11)
#    assert job_dict['863553'].submission_time, datetime.datetime(2013, 5, 23, 10, 42, 11)
#
#    assert job_dict['863100'].annotation == 'Resources'
#    assert job_dict['863100'].num_machines == 32
#    assert job_dict['863100'].num_mpiprocs == 1024
#    assert job_dict['863100'].queue_name == 'normal'
#
#    assert job_dict['861352'].title == 'Pressure_PBEsol_0'
#
#    assert job_dict['863554'].requested_wallclock_time_seconds is None
#
#    # allocated_machines is not implemented in this version of the plugin
#    #        for j in job_list:
#    #            if j.allocated_machines:
#    #                num_machines = 0
#    #                num_mpiprocs = 0
#    #                for n in j.allocated_machines:
#    #                    num_machines += 1
#    #                    num_mpiprocs += n.num_mpiprocs
#    #
#    #                self.assertTrue( j.num_machines==num_machines )
#    #                self.assertTrue( j.num_mpiprocs==num_mpiprocs )
#
#def test_parse_failed_squeue_output(self):
#    """Test that _parse_joblist_output reacts as expected to failures."""
#    scheduler = SlurmScheduler()
#
#    # non-zero return value should raise
#    with pytest.raises(SchedulerError, match='squeue returned exit code 1'):
#        scheduler._parse_joblist_output(1, TEXT_SQUEUE_TO_TEST, '')
#
#    # non-empty stderr should be logged
#    with self.assertLogs(scheduler.logger, logging.WARNING):
#        scheduler._parse_joblist_output(0, TEXT_SQUEUE_TO_TEST, 'error message')
#
#
#@pytest.mark.parametrize(
#    'value,expected',
#    [
#        ('2', 2 * 60),
#        ('02', 2 * 60),
#        ('02:3', 2 * 60 + 3),
#        ('02:03', 2 * 60 + 3),
#        ('1:02:03', 3600 + 2 * 60 + 3),
#        ('01:02:03', 3600 + 2 * 60 + 3),
#        ('1-3', 86400 + 3 * 3600),
#        ('01-3', 86400 + 3 * 3600),
#        ('01-03', 86400 + 3 * 3600),
#        ('1-3:5', 86400 + 3 * 3600 + 5 * 60),
#        ('01-3:05', 86400 + 3 * 3600 + 5 * 60),
#        ('01-03:05', 86400 + 3 * 3600 + 5 * 60),
#        ('1-3:5:7', 86400 + 3 * 3600 + 5 * 60 + 7),
#        ('01-3:05:7', 86400 + 3 * 3600 + 5 * 60 + 7),
#        ('01-03:05:07', 86400 + 3 * 3600 + 5 * 60 + 7),
#        ('UNLIMITED', 2**31 - 1),
#        ('NOT_SET', None),
#    ],
#)
#def test_time_conversion(value, expected):
#    """Test conversion of (relative) times.
#
#    From docs, acceptable time formats include
#    "minutes", "minutes:seconds", "hours:minutes:seconds",
#    "days-hours", "days-hours:minutes" and "days-hours:minutes:seconds".
#    """
#    scheduler = SlurmScheduler()
#    assert scheduler._convert_time(value) == expected
#
#
#def test_time_conversion_errors(caplog):
#    """Test conversion of (relative) times for bad inputs."""
#    scheduler = SlurmScheduler()
#
#    # Disable logging to avoid excessive output during test
#    with caplog.at_level(logging.CRITICAL):
#        with pytest.raises(ValueError, match='Unrecognized format for time string.'):
#            # Empty string not valid
#            scheduler._convert_time('')
#        with pytest.raises(ValueError, match='Unrecognized format for time string.'):
#            # there should be something after the dash
#            scheduler._convert_time('1-')
#        with pytest.raises(ValueError, match='Unrecognized format for time string.'):
#            # there should be something after the dash
#            # there cannot be a dash after the colons
#            scheduler._convert_time('1:2-3')

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
    job_tmpl.shebang = '#!/bin/bash'
    job_tmpl.uuid = str(uuid.uuid4())
    job_tmpl.job_resource = scheduler.create_job_resource(num_cpus=2, memory_mb=256)
    job_tmpl.max_wallclock_seconds = 24 * 3600
    tmpl_code_info = JobTemplateCodeInfo()
    tmpl_code_info.cmdline_params = ['mpirun', '-np', '4', 'pw.x', '-npool', '1']
    tmpl_code_info.stdin_name = 'aiida.in'
    job_tmpl.codes_info = [tmpl_code_info]
    job_tmpl.codes_run_mode = CodeRunMode.SERIAL

    submit_script_text = scheduler.get_submit_script(job_tmpl)
    
    assert submit_script_text == VALID_SCRIPT_CONTENT

def test_submit_script_mem_not_specified():
    """Test if memory_mb not pass to resource, it will not specified in job script"""
    scheduler = HyperQueueScheduler()

    job_tmpl = JobTemplate()
    job_tmpl.shebang = '#!/bin/bash'
    job_tmpl.uuid = str(uuid.uuid4())
    job_tmpl.job_resource = scheduler.create_job_resource(num_cpus=2)
    job_tmpl.max_wallclock_seconds = 24 * 3600
    tmpl_code_info = JobTemplateCodeInfo()
    tmpl_code_info.cmdline_params = ['mpirun', '-np', '4', 'pw.x', '-npool', '1']
    tmpl_code_info.stdin_name = 'aiida.in'
    job_tmpl.codes_info = [tmpl_code_info]
    job_tmpl.codes_run_mode = CodeRunMode.SERIAL

    submit_script_text = scheduler.get_submit_script(job_tmpl)

    assert "#HQ --resource mem" not in submit_script_text

def test_submit_script_is_hq_valid(hq_env: HqEnv):
    """The generated script can actually be run by hq"""
    scheduler = HyperQueueScheduler()

    job_tmpl = JobTemplate()
    job_tmpl.job_name = 'echo hello'
    job_tmpl.shebang = '#!/bin/bash'
    job_tmpl.uuid = str(uuid.uuid4())
    job_tmpl.job_resource = scheduler.create_job_resource(num_cpus=1)
    job_tmpl.max_wallclock_seconds = 24 * 3600
    tmpl_code_info = JobTemplateCodeInfo()
    tmpl_code_info.cmdline_params = ['echo', 'Hello']
    job_tmpl.codes_info = [tmpl_code_info]
    job_tmpl.codes_run_mode = CodeRunMode.SERIAL

    submit_script_text = scheduler.get_submit_script(job_tmpl)

    hq_env.start_server()
    hq_env.start_worker(cpus="2")
    Path("_aiidasubmit.sh").write_text(submit_script_text)
    hq_env.command(["submit", "_aiidasubmit.sh"])
    table = hq_env.command(["job", "info", "1"], as_table=True)

    assert table.get_row_value("Name") == "echo hello"
    assert "cpus: 1 compact" in table.get_row_value("Resources")

    wait_for_job_state(hq_env, 1, "FINISHED")
    
    assert table.get_row_value("State") == "FINISHED"

#class TestJoblistCommand:
#    """Tests of the issued squeue command."""
#
#    def test_joblist_single(self):
#        """Test that asking for a single job results in duplication of the list."""
#        scheduler = SlurmScheduler()
#
#        command = scheduler._get_joblist_command(jobs=['123'])
#        assert '123,123' in command
#
#    def test_joblist_multi(self):
#        """Test that asking for multiple jobs does not result in duplications."""
#        scheduler = SlurmScheduler()
#
#        command = scheduler._get_joblist_command(jobs=['123', '456'])
#        assert '123,456' in command
#        assert '456,456' not in command
#
#
#def test_parse_out_of_memory():
#    """Test that for job that failed due to OOM `parse_output` return the `ERROR_SCHEDULER_OUT_OF_MEMORY` code."""
#    scheduler = SlurmScheduler()
#    stdout = ''
#    stderr = ''
#    detailed_job_info = {
#        'retval': 0,
#        'stderr': '',
#        'stdout': 'Account|State|\nroot|OUT_OF_MEMORY|\n',
#    }
#
#    exit_code = scheduler.parse_output(detailed_job_info, stdout, stderr)
#    assert exit_code == CalcJob.exit_codes.ERROR_SCHEDULER_OUT_OF_MEMORY
#
#
#def test_parse_node_failure():
#    """Test that `ERROR_SCHEDULER_NODE_FAILURE` code is returned if `STATE == NODE_FAIL`."""
#    scheduler = SlurmScheduler()
#    detailed_job_info = {
#        'retval': 0,
#        'stderr': '',
#        'stdout': 'Account|State|\nroot|NODE_FAIL|\n',
#    }
#
#    exit_code = scheduler.parse_output(detailed_job_info, '', '')
#    assert exit_code == CalcJob.exit_codes.ERROR_SCHEDULER_NODE_FAILURE
#
#
#@pytest.mark.parametrize(
#    'detailed_job_info, expected',
#    [
#        ('string', TypeError),  # Not a dictionary
#        ({'stderr': ''}, ValueError),  # Key `stdout` missing
#        ({'stdout': None}, TypeError),  # `stdout` is not a string
#        ({'stdout': ''}, ValueError),  # `stdout` does not contain at least two lines
#        (
#            {'stdout': 'Account|State|\nValue|'},
#            ValueError,
#        ),  # `stdout` second line contains too few elements separated by pipe
#    ],
#)
#def test_parse_output_invalid(detailed_job_info, expected):
#    """Test `SlurmScheduler.parse_output` for various invalid arguments."""
#    scheduler = SlurmScheduler()
#
#    with pytest.raises(expected):
#        scheduler.parse_output(detailed_job_info, '', '')
#
#
#def test_parse_output_valid():
#    """Test `SlurmScheduler.parse_output` for valid arguments."""
#    detailed_job_info = {'stdout': 'State|Account|\n||\n'}
#    scheduler = SlurmScheduler()
#    assert scheduler.parse_output(detailed_job_info, '', '') is None
#
#
#def test_parse_submit_output_invalid_account():
#    """Test ``SlurmScheduler._parse_submit_output`` returns exit code if stderr contains error about invalid account."""
#    scheduler = SlurmScheduler()
#    stderr = 'Batch job submission failed: Invalid account or account/partition combination specified'
#    result = scheduler._parse_submit_output(1, '', stderr)
#    assert result == CalcJob.exit_codes.ERROR_SCHEDULER_INVALID_ACCOUNT
