[![Build Status](https://github.com/aiidateam/aiida-hyperqueue/workflows/ci/badge.svg?branch=main)](https://github.com/aiidateam/aiida-hyperqueue/actions)
[![Docs status](https://readthedocs.org/projects/aiida-hyperqueue/badge)](http://aiida-hyperqueue.readthedocs.io/)
[![PyPI version](https://badge.fury.io/py/aiida-hyperqueue.svg)](https://badge.fury.io/py/aiida-hyperqueue)

# AiiDA HyperQueue plugin

AiiDA plugin for the [HyperQueue](https://github.com/It4innovations/hyperqueue) metascheduler.

| ❗️ This package is still in the early stages of development and we will most likely break the API regularly in new 0.X versions. Be sure to pin the version when installing this package in scripts.|
|---|

## Features

Allows task farming on Slurm machines through the submission of AiiDA calculations to the [HyperQueue](https://github.com/It4innovations/hyperqueue) metascheduler.
See the [Documentation](http://aiida-hyperqueue.readthedocs.io/) for more information on how to install and use the plugin.

## For developers

To control the loglevel of command, since we use the `echo` module from aiida, the CLI loglever can be set through `logging.verdi_loglevel`.
