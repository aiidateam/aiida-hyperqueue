# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plugin for the HyperQueue meta scheduler."""

import json
import typing as t
import warnings

from aiida.common.extendeddicts import AttributeDict
from aiida.schedulers import Scheduler, SchedulerError, BashCliScheduler
from aiida.schedulers.datastructures import JobInfo, JobState, JobResource, JobTemplate

# Mapping of HyperQueue states to AiiDA `JobState`s
_MAP_STATUS_HYPERQUEUE = {
    "WAITING": JobState.QUEUED,
    "RUNNING": JobState.RUNNING,
    "FAILED": JobState.DONE,
    "CANCELED": JobState.DONE,
    "FINISHED": JobState.DONE,
}


class AiiDAHypereQueueDeprecationWarning(Warning):
    """Class for HypereQueue plugin deprecations."""


class HyperQueueJobResource(JobResource):
    """Class for HyperQueue job resources."""

    _default_fields = ("num_cpus", "memory_mb")

    _features = {
        "can_query_by_user": False,
    }

    def __init__(self, **kwargs):
        """Initialize the job resources from the passed arguments (the valid keys can be
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
            resources.num_cpus = kwargs.pop("num_cpus")
        except KeyError:
            try:
                # For backward compatibility where `num_machines` and `num_mpiprocs_per_machine` are setting
                # TODO: I only setting the default value as 1 for `num_mpiprocs_per_machine` because aiida-quantumespresso override
                # resources default with `num_machines` set to 1 and then get builder with such setting.
                # The `num_mpiprocs_per_machine` sometime can be read from "Default #procs/machine" of computer setup but if it is not exist
                # the builder can not be properly get without passing `option` to builder generator.
                # It is anyway a workaround for backward compatibility so this default is implemented despite it is quite specific for the qe plugin.
                resources.num_cpus = kwargs.pop("num_machines") * kwargs.pop(
                    "num_mpiprocs_per_machine", 1
                )
            except KeyError:
                raise KeyError(
                    "Must specify `num_cpus`, or (`num_machines` and `num_mpiprocs_per_machine`)"
                )
            else:
                message = "The `num_machines` and `num_mpiprocs_per_machine` for setting hyperqueue resources are deprecated. "
                "Please set `num_cpus` and `memory_mb`."

                message = f"{message} (this will be removed in aiida-hyperqueue v1.0)"
                warnings.warn(message, AiiDAHypereQueueDeprecationWarning, stacklevel=3)
        else:
            if not isinstance(resources.num_cpus, int):
                raise ValueError("`num_cpus` must be an integer")

        try:
            resources.memory_mb = kwargs.pop("memory_mb")
        except KeyError:
            resources.memory_mb = None  # Use all availble the memory on the worker
        else:
            if not isinstance(resources.memory_mb, int):
                raise ValueError("`memory_mb` must be an integer")

        return resources

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls):
        """Return True if this subclass accepts a `default_mpiprocs_per_machine` key, False otherwise."""
        return False

    def get_tot_num_mpiprocs(self):
        """Return the total number of cpus of this job resource."""
        return self.num_cpus


class HyperQueueScheduler(BashCliScheduler):
    """Support for the HyperQueue scheduler (https://it4innovations.github.io/hyperqueue/stable/)."""

    _logger = Scheduler._logger.getChild("hyperqueue")

    # Query only by list of jobs and not by user
    _features = {
        "can_query_by_user": False,
    }

    # The class to be used for the job resource.
    _job_resource_class = HyperQueueJobResource

    def _get_submit_script_header(self, job_tmpl: JobTemplate) -> str:
        """Return the submit script header, using the parameters from the
        job_tmpl.

        Args:
           job_tmpl: an JobTemplate instance with relevant parameters set.
        """
        hq_options = []
        prefix = "#HQ"

        if job_tmpl.job_name:
            hq_options.append(f'{prefix} --name="{job_tmpl.job_name}"')

        if job_tmpl.sched_output_path:
            hq_options.append(f"{prefix} --stdout={job_tmpl.sched_output_path}")

        if job_tmpl.sched_error_path:
            hq_options.append(f"{prefix} --stderr={job_tmpl.sched_error_path}")

        if job_tmpl.max_wallclock_seconds:
            # `--time-request` will only let the HQ job start on the worker in case there is still enough time available
            # `--time-limit` means the HQ job will be killed after this time.
            # It's better to use both: the former will guarantee that the time is still available, the latter
            # will kill job the job in case the job takes more time (e.g. it hangs).
            # This is the typical behavior of schedulers and avoids that if one run enters an infinite loop,
            # it burns all the time of the worker.
            hq_options.append(
                f"{prefix} --time-request={job_tmpl.max_wallclock_seconds}s"
            )
            hq_options.append(
                f"{prefix} --time-limit={job_tmpl.max_wallclock_seconds}s"
            )

        if job_tmpl.priority:
            # HQ jobs can be assigned priority, where jobs with a higher priority will be executed first. The default
            # priority is 0.
            hq_options.append(f"{prefix} --priority={job_tmpl.priority}")

        hq_options.append(f"{prefix} --cpus={job_tmpl.job_resource.num_cpus}")

        mem = job_tmpl.job_resource.memory_mb
        if mem is not None:
            hq_options.append(f"{prefix} --resource mem={mem}")

        return "\n".join(hq_options)

    def _get_submit_command(self, submit_script: str) -> str:
        """Return the string to execute to submit a given script.

        Args:
            submit_script: the path of the submit script relative to the working
                directory.
        """
        submit_command = f"hq submit --output-mode=json {submit_script}"

        self.logger.info(f"Submitting with: {submit_command}")

        return submit_command

    def _parse_submit_output(self, retval: int, stdout: str, stderr: str) -> str:
        """Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.

        Return a string with the JobID.
        """
        if retval != 0:
            self.logger.error(
                f"Error in _parse_submit_output: retval={retval}; stdout={stdout}; stderr={stderr}"
            )
            raise SchedulerError(
                f"Error during submission, retval={retval}\nstdout={stdout}\nstderr={stderr}"
            )

        try:
            transport_string = f" for {self.transport}"
        except SchedulerError:
            transport_string = ""

        if stderr.strip():
            self.logger.warning(
                f"in _parse_submit_output{transport_string}: there was some text in stderr: {stderr}"
            )

        try:
            hq_job_dict = json.loads(stdout)
            return str(hq_job_dict["id"])
        except Exception:
            # If no valid line is found, log and raise an error
            self.logger.error(
                f"in _parse_submit_output{transport_string}: unable to find the job id: {stdout}"
            )
            raise SchedulerError(
                "Error during submission, could not retrieve the jobID from "
                "hq submit output; see log for more info."
            )

    def _get_joblist_command(
        self, jobs: t.Optional[list] = None, user: t.Optional[str] = None
    ) -> str:
        """Return the ``hq`` command for listing the active jobs.

        Note: since the ``hq job list`` command cannot filter on job ids (yet), the ``jobs`` input is currently ignored.
        These could in principle be passed to the ``hq job`` command, but this has an entirely different format.
        """

        return "hq job list --filter waiting,running --output-mode=json"

    def _parse_joblist_output(self, retval: int, stdout: str, stderr: str) -> list:
        """Parse the stdout for the joblist command.

        :return: A ``List`` of ``JobInfo`` instances.
        """
        if retval != 0:
            raise SchedulerError(
                f"""hq job list returned exit code {retval} (_parse_joblist_output function)
                stdout='{stdout.strip()}'
                stderr='{stderr.strip()}'
                """
            )

        if stderr.strip():
            self.logger.warning(
                f"`hq job list` returned exit code 0 (_parse_joblist_output function) but non-empty stderr='{stderr.strip()}'"
            )

        # convert hq returned job list to job info list
        # HQ support 1 hq job with multiple tasks.
        # Since the way aiida-hq using hq is 1-1 match between hq job and hq task, we only parse 1 task as aiida job.
        hq_job_info_list = json.loads(stdout)

        job_info_list = []
        for hq_job_dict in hq_job_info_list:
            job_info = JobInfo()
            job_info.job_id = str(
                hq_job_dict["id"]
            )  # must be str, if it is a int job will not waiting
            job_info.title = hq_job_dict["name"]
            stats: t.List[str] = [
                stat for stat, v in hq_job_dict["task_stats"].items() if v > 0
            ]
            if hq_job_dict["task_count"] != 1 or len(stats) != 1:
                self.logger.error("not able to parse hq job with multiple tasks.")
            else:
                job_info.job_state = _MAP_STATUS_HYPERQUEUE[stats[0].upper()]

            job_info_list.append(job_info)

            # TODO: In principle more detailed information can be parsed for each job by `hq job info`, such as cpu, wall_time etc.

        return job_info_list

    def _get_kill_command(self, jobid):
        """Return the command to kill the job with specified jobid."""
        submit_command = f"hq job cancel {jobid}"

        self.logger.info(f"killing job {jobid}")

        return submit_command

    def _parse_kill_output(self, retval, stdout, stderr):
        """Parse the output of the kill command.

        :return: True if everything seems ok, False otherwise.
        """
        if retval != 0:
            self.logger.error(
                f"Error in _parse_kill_output: retval={retval}; stdout={stdout}; stderr={stderr}"
            )
            return False

        try:
            transport_string = f" for {self.transport}"
        except SchedulerError:
            transport_string = ""

        if "ERROR" in stderr:
            self.logger.warning(
                f"in _parse_kill_output{transport_string}: there was an error when trying to cancel the job: {stderr}"
            )
            return False

        return True

    def _get_detailed_job_info_command(self, job_id: str) -> dict[str, t.Any]:
        """Return the command to run to get the detailed information on a job,
        even after the job has finished.

        The output text is just retrieved, and returned for logging purposes.
        `jq` is used to transform the json into a one-line string.
        """
        return f"hq job info {job_id} --output-mode json | jq -c ."
