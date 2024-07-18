# The [`aiida-hyperqueue`](http://github.com/aiidateam/aiida-hyperqueue) plugin for [AiiDA]

`aiida-hyperqueue` is a scheduler plugin for AiiDA for running workflows using the [HyperQueue] metascheduler.

## Installation

For now the plugin can only be installed directly from the GitHub repository:

```
git clone https://github.com/aiidateam/aiida-hyperqueue
pip install -e aiida-hyperqueue
```

Further setup and usage instructions can be found on the {ref}`getting-started` page.

:::{important}

`aiida-hyperqueue` is currently still in an alpha stage and under heavy development!
There likely are bugs, and the API is likely to still change significantly before it stabilizes.
Take care in using it for your production runs.

:::

## Acknowledgements

:::{admonition} TODO

Update the acknowledgements.

:::

`aiida-hyperqueue` is released under the MIT license.
If you use this plugin for your research, please cite the following work:

```{eval-rst}
.. highlights:: Jakub Beránek, Ada Böhm, Gianluca Palermo, Jan Martinovič, and Branislav Jansík, *HyperQueue: Efficient and ergonomic task graphs on HPC clusters*, SoftwareX 27, 101814 (2024); https://doi.org/10.1016/j.softx.2024.101814; https://it4innovations.github.io/hyperqueue/stable/.
```

If you use AiiDA for your research, please cite the following work:

```{eval-rst}
.. highlights:: Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari,
  and Boris Kozinsky, *AiiDA: automated interactive infrastructure and database
  for computational science*, Comp. Mat. Sci 111, 218-230 (2016);
  https://doi.org/10.1016/j.commatsci.2015.09.013; http://www.aiida.net.
```

## Contents

```{toctree}
:maxdepth: 2

get_started
developer_guide/index
```

Please contact <mailto:developers@aiida.net> for information concerning `aiida-hyperqueue` and the [AiiDA mailing list](http://www.aiida.net/mailing-list/) for questions concerning `aiida`.

<!-- - {ref}`search` -->

[aiida]: http://www.aiida.net
[HyperQueue]: https://it4innovations.github.io/hyperqueue/stable/
