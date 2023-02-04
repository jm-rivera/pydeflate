from typing import Callable

import pytest

from pydeflate.get_data import imf_data
import os
from pydeflate.pydeflate_config import PYDEFLATE_PATHS


def test_update():
    test_obj = imf_data.IMF()

    # Download an older version
    test_obj.update(latest_r=1, latest_y=2022)

    # Fail test if the file doesn't exist
    if not os.path.exists(PYDEFLATE_PATHS.data / "weo2022_1.csv"):
        assert False

    os.remove(PYDEFLATE_PATHS.data / "weo2022_1.csv")


def test_load_data():
    test_obj = imf_data.IMF()

    # Load most recent saved data
    test_obj.load_data()

    assert len(test_obj.data) > 0


def test_inflation_acp():
    test_obj = imf_data.IMF()
    test_obj.load_data()

    d = test_obj.inflation_acp()

    assert len(d) > 0
    assert d.iso_code.nunique() > 20


def test_inflation_epcp():
    test_obj = imf_data.IMF()
    test_obj.load_data()

    d = test_obj.inflation_epcp()

    assert len(d) > 0
    assert d.iso_code.nunique() > 20


def test_inflation_gdp():
    test_obj = imf_data.IMF()
    test_obj.load_data()

    d = test_obj.inflation_gdp()

    assert len(d) > 0
    assert d.iso_code.nunique() > 20


def test_available_methods():
    test_obj = imf_data.IMF()

    # Test that the dictionary contains more than one method
    assert len(test_obj.available_methods()) > 1

    # Test that the keys and values match their respective types
    for k, v in test_obj.available_methods().items():
        assert isinstance(k, str)
        assert isinstance(v, Callable)


def test_get_deflator():
    test_obj = imf_data.IMF(method="gdp")
    test_obj.load_data()

    # get gdp deflator
    gdp_def = test_obj.inflation_gdp()

    assert all(gdp_def == test_obj.get_deflator())
