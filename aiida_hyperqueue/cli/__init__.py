# -*- coding: utf-8 -*-
from aiida.cmdline.params import options as core_options
from aiida.cmdline.params import types as core_types

from .root import cmd_root
from .install import cmd_install
from .server import cmd_info, cmd_start, cmd_stop
from .alloc import cmd_list, cmd_add, cmd_remove
