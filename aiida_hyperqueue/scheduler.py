# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Plugin for the HyperQueue meta scheduler.
"""
import re
from typing import Union

from aiida.common.extendeddicts import AttributeDict
from aiida.common.exceptions import FeatureNotAvailable
from aiida.schedulers import Scheduler, SchedulerError
from aiida.schedulers.datastructures import JobInfo, JobState, JobResource, JobTemplate

# Mapping of HyperQueue states to AiiDA `JobState`s
_MAP_STATUS_HYPERQUEUE = {
    'WAITING': JobState.QUEUED,
    'RUNNING': JobState.RUNNING,
    'FAILED': JobState.DONE,
    'CANCELED': JobState.DONE,
    'FINISHED': JobState.DONE,
}


class HyperQueueJobResource(JobResource):
    """Class for HyperQueue job resources."""

    _default_fields = ('num_mpiprocs', 'num_cores', 'memory_Mb')

    def __init__(self, **kwargs):
        """
        Initialize the job resources from the passed arguments (the valid keys can be
        obtained with the function self.get_valid_keys()).

        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = self.validate_resources(**kwargs)
        super().__init__(resources)

    @classmethod
    def validate_resources(cls, **kwargs):
        """Validate the resources against the job resource class of this scheduler.

        :param kwargs: dictionary of values to define the job resources
        :return: attribute dictionary with the parsed parameters populated
        :raises ValueError: if the resources are invalid or incomplete
        """

        resources = AttributeDict()

        try:
            resources.num_cores = int(kwargs.pop('num_cores'))
        except (KeyError, ValueError) as exception:
            raise ValueError(
                '`num_cores` must be specified and must be an integer'
            ) from exception

        try:
            resources.num_mpiprocs = int(kwargs.pop('num_mpiprocs'))
        except KeyError:
            resources.num_mpiprocs = int(resources.num_cores)
        except ValueError as exception:
            raise ValueError(
                '`num_mpiprocs` must be an integer') from exception

        try:
            resources.memory_Mb = int(kwargs.pop('memory_Mb'))
        except KeyError:
            resources.memory_Mb = 0  # Use all the memory on the node
        except ValueError as exception:
            raise ValueError('`memory_Mb` must be an integer') from exception

        return resources

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls):
        """Return True if this subclass accepts a `default_mpiprocs_per_machine` key, False otherwise."""
        return True

    def get_tot_num_mpiprocs(self):
        """Return the total number of cpus of this job resource."""
        return self.num_mpiprocs


class HyperQueueScheduler(Scheduler):
    """
    Support for the HyperQueue scheduler (https://it4innovations.github.io/hyperqueue/stable/).
    """
    _logger = Scheduler._logger.getChild('hyperqueue')

    # Query only by list of jobs and not by user
    _features = {
        'can_query_by_user': False,
    }

    # The class to be used for the job resource.
    _job_resource_class = HyperQueueJobResource

    def _get_submit_script_header(self, job_tmpl: JobTemplate) -> str:
        """
        Return the submit script header, using the parameters from the
        job_tmpl.

        Args:
           job_tmpl: an JobTemplate instance with relevant parameters set.
        """
        hq_options = []

        if job_tmpl.job_name:
            hq_options.append(f'--name="{job_tmpl.job_name}"')

        if job_tmpl.sched_output_path:
            hq_options.append(f'--stdout={job_tmpl.sched_output_path}')

        if job_tmpl.sched_error_path:
            hq_options.append(f'--stderr={job_tmpl.sched_error_path}')

        if job_tmpl.max_wallclock_seconds:
            # `--time-request` will only let the HQ job start on the worker in case there is still enough time available
            # `--time-limit` means the HQ job will be killed after this time.
            # It's better to use both: the former will guarantee that the time is still available, the latter
            # will kill job the job in case the job takes more time (e.g. it hangs).
            # This is the typical behavior of schedulers and avoids that if one run enters an infinite loop,
            # it burns all the time of the worker.
            hq_options.append(
                f'--time-request={job_tmpl.max_wallclock_seconds}s --time-limit={job_tmpl.max_wallclock_seconds}s'
            )

        if job_tmpl.priority:
            # HQ jobs can be assigned priority, where jobs with a higher priority will be executed first. The default
            # priority is 0.
            hq_options.append(f'--priority={job_tmpl.priority}')

        if job_tmpl.job_resource.num_cores:
            hq_options.append(f'--cpus={job_tmpl.job_resource.num_cores}')

        return '#HQ ' + ' '.join(hq_options)

    def _get_submit_command(self, submit_script: str) -> str:
        """
        Return the string to execute to submit a given script.

        Args:
            submit_script: the path of the submit script relative to the working
                directory.
        """
        submit_command = (
            f"chmod 774 {submit_script}; options=$(grep '#HQ' {submit_script});"
            f"sed -i s/\\'srun\\'/srun\ --cpu-bind=map_cpu:\$HQ_CPUS/  {submit_script};"
            f'hq job submit ${{options:3}} ./{submit_script}')

        self.logger.info(f'submitting with: {submit_command}')

        return submit_command

    def _parse_submit_output(self, retval: int, stdout: str,
                             stderr: str) -> str:
        """
        Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.

        Return a string with the JobID.
        """
        if retval != 0:
            self.logger.error(
                f'Error in _parse_submit_output: retval={retval}; stdout={stdout}; stderr={stderr}'
            )
            raise SchedulerError(
                f'Error during submission, retval={retval}\nstdout={stdout}\nstderr={stderr}'
            )

        try:
            transport_string = f' for {self.transport}'
        except SchedulerError:
            transport_string = ''

        if stderr.strip():
            self.logger.warning(
                f'in _parse_submit_output{transport_string}: there was some text in stderr: {stderr}'
            )

        job_id_pattern = re.compile(
            r'Job\ssubmitted\ssuccessfully,\sjob\sID:\s(?P<jobid>\d+)')

        for line in stdout.split('\n'):
            match = job_id_pattern.match(line.strip())
            if match:
                return match.group('jobid')

        # If no valid line is found, log and raise an error
        self.logger.error(
            f'in _parse_submit_output{transport_string}: unable to find the job id: {stdout}'
        )
        raise SchedulerError(
            'Error during submission, could not retrieve the jobID from '
            'hq submit output; see log for more info.')

    def _get_joblist_command(self,
                             jobs: Union[str, list, tuple] = None,
                             user: str = None) -> str:
        """
        Return the ``hq`` command for listing the active jobs.

        Note: since the ``hq job list`` command cannot filter on job ids (yet), the ``jobs`` input is currently ignored.
        These could in principle be passed to the ``hq job`` command, but this has an entirely different format.
        """

        if user:
            raise FeatureNotAvailable('Cannot query by user with HyperQueue')

        return 'hq job list --filter waiting,running'

    def _parse_joblist_output(self, retval: int, stdout: str,
                              stderr: str) -> list:
        """
        Parse the stdout for the joblist command.

        :return: A ``List`` of ``JobInfo`` instances.
        """
        if retval != 0:
            raise SchedulerError(
                f"""hq job list returned exit code {retval} (_parse_joblist_output function)
                stdout='{stdout.strip()}'
                stderr='{stderr.strip()}'
                """)

        if stderr.strip():
            self.logger.warning(
                f"hq job list returned exit code 0 (_parse_joblist_output function) but non-empty stderr='{stderr.strip()}'"
            )

        job_info_pattern = re.compile(
            r'\|\s+(?P<id>[\d]+)\s\|\s+(?P<name>[^|]+)\s+\|\s(?P<state>[\w]+)\s+\|\s(?P<tasks>[\d]+)\s+\|'
        )
        job_info_list = []

        for line in stdout.split('\n'):
            match = job_info_pattern.match(line)
            if match:
                job_dict = match.groupdict()
                job_info = JobInfo()
                job_info.job_id = job_dict['id']
                job_info.title = job_dict['name']
                job_info.job_state = _MAP_STATUS_HYPERQUEUE[
                    job_dict['state'].upper()]
                job_info_list.append(job_info)

        return job_info_list

    def _get_kill_command(self, jobid):
        """
        Return the command to kill the job with specified jobid.
        """
        submit_command = f'hq job cancel {jobid}'

        self.logger.info(f'killing job {jobid}')

        return submit_command

    def _parse_kill_output(self, retval, stdout, stderr):
        """
        Parse the output of the kill command.

        :return: True if everything seems ok, False otherwise.
        """
        if retval != 0:
            self.logger.error(
                f'Error in _parse_kill_output: retval={retval}; stdout={stdout}; stderr={stderr}'
            )
            return False

        try:
            transport_string = f' for {self.transport}'
        except SchedulerError:
            transport_string = ''

        if 'ERROR' in stderr:
            self.logger.warning(
                f'in _parse_kill_output{transport_string}: there was an error when trying to cancel the job: {stderr}'
            )
            return False

        return True
