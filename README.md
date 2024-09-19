[![Build Status](https://github.com/aiidateam/aiida-hyperqueue/workflows/ci/badge.svg)](https://github.com/aiidateam/aiida-hyperqueue/actions)
[![Docs status](https://readthedocs.org/projects/aiida-hyperqueue/badge)](http://aiida-hyperqueue.readthedocs.io/)
[![PyPI version](https://badge.fury.io/py/aiida-hyperqueue.svg)](https://badge.fury.io/py/aiida-hyperqueue)

# AiiDA HyperQueue plugin

AiiDA plugin for the [HyperQueue](https://it4innovations.github.io/hyperqueue/stable/) metascheduler.

| ❗️ This package is still in the early stages of development and we will most likely break the API regularly in new 0.X versions. Be sure to pin the version when installing this package in scripts.|
|---|

## Features

Allows task farming on Slurm machines through the submission of AiiDA calculations to the [HyperQueue](https://github.com/It4innovations/hyperqueue) metascheduler.
See the [Documentation](http://aiida-hyperqueue.readthedocs.io/) for more information on how to install and use the plugin.

## For developers

To control the loglevel of command, since we use the `echo` module from aiida, the CLI loglever can be set through `logging.verdi_loglevel`.

## Acknowledgenement
If you use this plugin for your research, please cite the following work:

#### HyperQueue

* J. Beránek *et al.*, *HyperQueue: Efficient and ergonomic task graphs on HPC clusters*, SoftwareX **27**, 101814 (2024); DOI: [10.1016/j.softx.2024.101814](https://doi.org/10.1016/j.softx.2024.101814)

#### AiiDA

* S. P. Huber *et al.*, *AiiDA 1.0, a scalable computational infrastructure for automated reproducible workflows and data provenance*, Scientific Data **7**, 300 (2020); DOI: [10.1038/s41597-020-00638-4](https://doi.org/10.1038/s41597-020-00638-4)
* M. Uhrin *et al.*, *Workflows in AiiDA: Engineering a high-throughput, event-based engine for robust and modular computational workflows*, Computational Materials Science **187**, 110086 (2021); DOI: [10.1016/j.commatsci.2020.110086](https://doi.org/10.1016/j.commatsci.2020.110086)
