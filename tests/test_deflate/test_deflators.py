#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 14 11:42:54 2021

@author: jorge
"""

"""Tests for `pydeflate` package."""

import pytest
import pandas as pd
import numpy as np


from pydeflate.deflate.deflators import (
    oecd_dac_deflators,
    wb_deflators,
    imf_deflators,
)

from tests.test_deflate import testing_parameters as tp


@pytest.mark.parametrize(*tp.dac_params)
def test_oecd_dac_deflators(byear, source, target, country, tyear, value) -> None:
    """Unit test for oecd_dac_deflators"""

    test = oecd_dac_deflators(byear, source, target)

    test_num = test.loc[
        (test.iso_code == country) & (test.year.dt.year == tyear)
    ].deflator.sum()

    assert int(np.floor(test_num)) == value


@pytest.mark.parametrize(*tp.dac_error_params)
def test_oecd_dac_deflators_errors(byear, source, target) -> None:
    """Unit test to check that function returns right parameter errors"""
    with pytest.raises(ValueError):
        oecd_dac_deflators(byear, source, target)


@pytest.mark.parametrize(*tp.wb_params)
def test_wb_deflators(base, method, source, target, country, tyear, value):
    """Unit test for wb_deflators"""
    test = wb_deflators(base, method, source, target)
    test_num = test.loc[
        (test.iso_code == country) & (test.year.dt.year == tyear)
    ].deflator.sum()

    assert int(np.floor(test_num)) == value


@pytest.mark.parametrize(*tp.wb_error_params)
def test_wb_deflators_errors(base, method, source, target, error):
    with pytest.raises(error):
        wb_deflators(base, method, source, target)


@pytest.mark.parametrize(*tp.imf_params)
def test_imf_deflators(base, method, source, target, country, tyear, value):
    """Unit test for wb_deflators"""
    test = imf_deflators(base, method, source, target)
    test_num = test.loc[
        (test.iso_code == country) & (test.year.dt.year == tyear)
    ].deflator.sum()

    assert int(np.floor(test_num)) == value


@pytest.mark.parametrize(*tp.imf_error_params)
def test_imf_deflators_errors(base, method, source, target, error):
    with pytest.raises(error):
        imf_deflators(base, method, source, target)
