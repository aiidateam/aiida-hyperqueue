(getting-started)=

# Getting started

The `aiida-hyperqueue` plugin provides an AiiDA scheduler for running calculations with task farming on machines that use the Slurm scheduler.
It relies on [HyperQueue] (HQ), which is a meta scheduler that runs on the cluster.
In short, HQ runs a server to which jobs can be submitted, which in turn are picked up by HQ workers that are run inside Slurm jobs.
`aiida-hyperqueue` simply allows you to submit calculation jobs to the HQ server.

## Installing HyperQueue on the cluster

After installing the plugin, there are a couple of setup steps you need to execute **on the cluster you want to run on** before you can start using the scheduler.
Since the scheduler relies on HyperQueue, it needs to be installed on the system.
You can find the installation instructions for HyperQueue [here](https://it4innovations.github.io/hyperqueue/stable/installation/), but we provide a quick list of commands you have to execute below.
First, make a directory where you want to store the binary, e.g. `$HOME/bin`:

:::{code-block} console

mkdir -p $HOME/bin

:::

Then download the latest version (`v0.18.0`) of HyperQueue, untar the binary and put it in the directory you just created:

:::{code-block} console

wget -qO- https://github.com/It4innovations/hyperqueue/releases/download/v0.18.0/hq-v0.18.0-linux-x64.tar.gz | tar xvz -C $HOME/bin
:::

For the older version of HyperQueue, you can change the version number in the URL.

Next, if the directory isn't already part of your `PATH`, add the following line to your `.bashrc`:

:::{code-block} console

export PATH=$HOME/bin:$PATH

:::

You should now be able to run the `hq` command from any directory.

## Setting up a new computer

Next, you need to set up a computer to run with the HyperQueue scheduler.
Below you can find an example YAML file:

:::{code-block} yaml

label: eiger-hq
description: Eiger CSCS cluster
hostname: eiger.cscs.ch
transport: core.ssh
scheduler: hyperqueue  # Use the `hyperqueue` scheduler
shebang: '#!/bin/bash'
work_dir: /capstor/scratch/cscs/{username}/aiida/
mpirun_command: srun -s -n {num_cpus} --mem {memory_mb}  # Make sure to use this srun command
mpiprocs_per_machine: 128
prepend_text: ' '
append_text: ' '

:::

Copy the contents into e.g. `eiger-hq.yaml`, adapt where necessary and set up the computer:

:::{code-block} console

verdi computer setup --config eiger-hq.yaml

:::

Next, configure the ssh transport for the computer with `verdi computer configure ssh eiger-hq`.

## Starting the HQ server

Next, we need to start the HQ server on the remote cluster.
One option would be to execute the correct command on the machine, you can find the instructions in the [HyperQueue documentation](https://it4innovations.github.io/hyperqueue/stable/deployment/server/).
However, the plugin also provides some helpful CLI commands that you can run from your AiiDA machine instead.
To start the server, simply run:

:::{code-block} console

aiida-hq server start eiger-hq

:::

You can get more information on the server using:

:::{code-block} console

$ aiida-hq server info eiger-hq
+-------------+-------------------------+
| Server UID  | 5yWtgC                  |
| Client host | eiger-ln002             |
| Client port | 32989                   |
| Worker host | eiger-ln002             |
| Worker port | 43041                   |
| Version     | v0.18.0                 |
| Pid         | 181310                  |
| Start date  | 2024-09-02 17:51:12 UTC |
+-------------+-------------------------+

:::

## HyperQueue Allocations

Now you can in principle start submitting jobs to the HQ server as you would typically do when running with AiiDA.
However, once the jobs are submitted to the HQ server, we still need to submit actual Slurm jobs that host the HQ workers, which in turn grab work from the server to execute.
One way to do this would be to submit these Slurm jobs manually, but this would be somewhat tedious since then we need to always make sure that we are running sufficient Slurm jobs for the work we have submitted to the HQ server.
Fortunately, HyperQueue allows you to configure *allocations* that will automatically start submitting jobs to the scheduler when there is work on the server, but no workers to execute it.

Once again, the [HyperQueue documentation](https://it4innovations.github.io/hyperqueue/stable/deployment/allocation/) describes this feature in full, but we have a CLI command for performing the basic operations needed to run the `aiida-hyperqueue` scheduler.
For example:

:::{code-block} console

aiida-hq alloc add -Y eiger-hq -t 30m -- -A mr0 -C mc -p debug

:::

Both the `-Y / --computer` option and `-t / --time-limit` options are required.
Use the `--hyper-threading` or `--no-hyper-threading` options to enable or disable hyper-threading for the worker allocation.
After the double hyphen `--`, you can place additional Slurm options to e.g. specify your project account (`-A`), constraints (`-C`) and the partition you want to run on (`-p`).
Once one or more allocations have been configured, you can check the list of allocations with `aiida-hq alloc list`:

:::{code-block} console

$ aiida-hq alloc list eiger-hq
+----+--------------+-------------------+-----------+---------+-------+-----------------------+
| ID | Backlog size | Workers per alloc | Timelimit | Manager | Name  | Args                  |
+----+--------------+-------------------+-----------+---------+-------+-----------------------+
| 1  | 1            | 1                 | 30m       | SLURM   | aiida | -A,mr0,-C,mc,-p,debug |
+----+--------------+-------------------+-----------+---------+-------+-----------------------+

:::

Finally, allocations can be removed with `aiida-hq alloc remove`:

:::{code-block} console

aiida-hq alloc remove -Y eiger-hq 1

:::

Note that you must pass the allocation `ID` to the remove command.


[HyperQueue]: https://it4innovations.github.io/hyperqueue/stable/
