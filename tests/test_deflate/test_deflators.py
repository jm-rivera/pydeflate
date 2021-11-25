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

import pandas as pd

# =============================================================================
# Deflators testing parameters
# =============================================================================


# OECD_DAC parameters
dac_params = (
    "byear,source,target,country,tyear,value",
    [
        (2018, "USA", "USA", "FRA", 2016, 92),
        (2016, "USA", "USA", "DEU", 2017, 103),
        (2019, "USA", "USA", "GBR", 2010, 102),
        (2019, "FRA", "FRA", "CAN", 2019, 100),
        (2010, "DEU", "DEU", "FRA", 2010, 100),
        (2020, "CAN", "GBR", "FRA", 2020, 172),
        (2020, "DEU", "GBR", "DEU", 2010, 95),
        (2020, "EUI", "USA", "EUI", 2015, 82),
        (2020, "USA", "ITA", "ITA", 2011, 126),
        (2013, "LCU", "USA", "USA", 2009, 93),
    ],
)

# OECD_DAC errors
dac_error_params = (
    "byear, source, target",
    [
        ("2018", "USA", "USA"),
        (2018, "XXX", "USA"),
        (2015, "USA", "XXX"),
        (2020, 2021, "USA"),
        (2025, "USA", "USA"),
    ],
)

# WB Parameters
wb_params = (
    "base, method, source, target, country, tyear, value",
    [
        (2018, "cpi", "USA", "USA", "FRA", 2016, 91),
        (2019, "cpi", "USA", "USA", "DEU", 2017, 97),
        (2019, "cpi", "USA", "USA", "GBR", 2010, 101),
        (2010, "cpi", "DEU", "DEU", "FRA", 2010, 100),
        (2020, "cpi", "CAN", "GBR", "FRA", 2020, 171),
        (2020, "cpi", "DEU", "GBR", "DEU", 2010, 98),
        (2020, "cpi", "USA", "ITA", "ITA", 2011, 129),
        (2018, "gdp", "USA", "USA", "FRA", 2016, 92),
        (2019, "gdp", "USA", "USA", "DEU", 2017, 96),
        (2019, "gdp", "USA", "USA", "GBR", 2010, 102),
        (2010, "gdp", "DEU", "DEU", "FRA", 2010, 100),
        (2020, "gdp", "CAN", "GBR", "FRA", 2020, 171),
        (2020, "gdp", "DEU", "GBR", "DEU", 2010, 95),
        (2020, "gdp", "USA", "ITA", "ITA", 2011, 126),
        (2018, "gdp_linked", "USA", "USA", "FRA", 2016, 92),
        (2019, "gdp_linked", "USA", "USA", "DEU", 2017, 97),
        (2019, "gdp_linked", "USA", "USA", "GBR", 2010, 102),
        (2010, "gdp_linked", "DEU", "DEU", "FRA", 2010, 100),
        (2019, "gdp_linked", "CAN", "GBR", "FRA", 2007, 149),
        (2019, "gdp_linked", "DEU", "GBR", "DEU", 2010, 98),
        (2019, "gdp_linked", "USA", "ITA", "ITA", 2011, 128),
        (2019, "gdp_linked", "LCU", "USA", "DEU", 2017, 85),
        (2005, "gdp_linked", "LCU", "FRA", "FRA", 2005, 100),
    ],
)

# WB Errors
wb_error_params = (
    "base, method, source, target, error",
    [
        (2020, "gdp_cpi", "USA", "FRA", ValueError),
        ("2020", "cpi", "USA", "FRA", ValueError),
        (2018, "cpi", "XXX", "FRA", ValueError),
        (2018, "gdp", "GBR", "XXX", ValueError),
        (2035, "gdp", "GBR", "FRA", ValueError),
    ],
)

# IMF_Parameters
imf_params = (
    "base, method, source, target, country, tyear, value",
    [
        (2018, "pcpi", "USA", "USA", "FRA", 2016, 90),
        (2019, "pcpi", "USA", "USA", "DEU", 2017, 97),
        (2019, "pcpi", "USA", "USA", "GBR", 2010, 100),
        (2010, "pcpi", "DEU", "DEU", "FRA", 2010, 100),
        (2020, "pcpi", "CAN", "GBR", "FRA", 2020, 171),
        (2020, "pcpi", "DEU", "GBR", "DEU", 2010, 98),
        (2020, "pcpi", "USA", "ITA", "ITA", 2011, 128),
        (2018, "gdp", "USA", "USA", "FRA", 2016, 92),
        (2019, "gdp", "USA", "USA", "DEU", 2017, 96),
        (2019, "gdp", "USA", "USA", "GBR", 2010, 102),
        (2010, "gdp", "DEU", "DEU", "FRA", 2010, 100),
        (2020, "gdp", "CAN", "GBR", "FRA", 2020, 171),
        (2020, "gdp", "DEU", "GBR", "DEU", 2010, 95),
        (2020, "gdp", "USA", "ITA", "ITA", 2011, 126),
        (2018, "pcpie", "USA", "USA", "FRA", 2016, 90),
        (2019, "pcpie", "USA", "USA", "DEU", 2017, 97),
        (2019, "pcpie", "USA", "USA", "GBR", 2010, 101),
        (2010, "pcpie", "DEU", "DEU", "FRA", 2010, 100),
        (2019, "pcpie", "CAN", "GBR", "FRA", 2007, 144),
        (2019, "pcpie", "DEU", "GBR", "DEU", 2010, 100),
        (2019, "pcpie", "USA", "ITA", "ITA", 2011, 130),
    ],
)

# IMF Errors
imf_error_params = (
    "base, method, source, target, error",
    [
        (2020, "gdp_cpi", "USA", "FRA", ValueError),
        ("2020", "pcpi", "USA", "FRA", ValueError),
        (2018, "pcpie", "XXX", "FRA", ValueError),
        (2018, "gdp", "GBR", "XXX", ValueError),
    ],
)


@pytest.mark.parametrize(*dac_params)
def test_oecd_dac_deflators(byear, source, target, country, tyear, value) -> None:
    """Unit test for oecd_dac_deflators"""

    test = oecd_dac_deflators(byear, source, target)

    test_num = test.loc[
        (test.iso_code == country) & (test.year.dt.year == tyear)
    ].deflator.sum()

    assert int(np.floor(test_num)) == value


@pytest.mark.parametrize(*dac_error_params)
def test_oecd_dac_deflators_errors(byear, source, target) -> None:
    """Unit test to check that function returns right parameter errors"""
    with pytest.raises(ValueError):
        oecd_dac_deflators(byear, source, target)


@pytest.mark.parametrize(*wb_params)
def test_wb_deflators(base, method, source, target, country, tyear, value):
    """Unit test for wb_deflators"""
    test = wb_deflators(base, method, source, target)
    test_num = test.loc[
        (test.iso_code == country) & (test.year.dt.year == tyear)
    ].deflator.sum()

    assert int(np.floor(test_num)) == value


@pytest.mark.parametrize(*wb_error_params)
def test_wb_deflators_errors(base, method, source, target, error):
    with pytest.raises(error):
        wb_deflators(base, method, source, target)


@pytest.mark.parametrize(*imf_params)
def test_imf_deflators(base, method, source, target, country, tyear, value):
    """Unit test for wb_deflators"""
    test = imf_deflators(base, method, source, target)
    test_num = test.loc[
        (test.iso_code == country) & (test.year.dt.year == tyear)
    ].deflator.sum()

    assert int(np.floor(test_num)) == value


@pytest.mark.parametrize(*imf_error_params)
def test_imf_deflators_errors(base, method, source, target, error):
    with pytest.raises(error):
        imf_deflators(base, method, source, target)
