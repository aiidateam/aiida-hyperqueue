# -*- coding: utf-8 -*-
"""Tests for command line interface."""

import pytest

from aiida_hyperqueue.scheduler import HyperQueueJobResource


def test_hyperqueue_resource():
    """Test construction of the FwResource object"""
    res = HyperQueueJobResource(num_cpus=16, memory_mb=20)
    assert res.num_cpus == 16
    assert res.memory_mb == 20

    with pytest.raises(ValueError):
        res = HyperQueueJobResource(foo="bar")
