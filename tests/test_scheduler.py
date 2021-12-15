# -*- coding: utf-8 -*-
""" Tests for command line interface.

"""
import pytest

from aiida_hyperqueue.scheduler import HyperQueueJobResource


def test_hyperqueue_resource():
    """Test construction of the FwResource object"""
    res = HyperQueueJobResource(num_mpiprocs=8, num_cores=16, memory_Mb=20)
    assert res.num_mpiprocs == 8
    assert res.num_cores == 16
    assert res.memory_Mb == 20

    with pytest.raises(ValueError):
        res = HyperQueueJobResource(foo='bar')
