#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 20 12:18:00 2021

@author: jorge
"""


import pytest

from pydeflate.get_data import wb_data
import sys
import io
import datetime


def test_update_indicators():

    """Capture print statements which are only printed if download successful"""

    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    wb_data.update_indicators()

    output = new_stdout.getvalue()

    sys.stdout = old_stdout

    print(output)

    assert (
        output
        == """Successfully updated NY.GDP.DEFL.ZS for 1950-2025
Successfully updated NY.GDP.DEFL.ZS.AD for 1950-2025
Successfully updated FP.CPI.TOTL for 1950-2025
Successfully updated PA.NUS.FCRF for 1950-2025
Successfully updated PX.REX.REER for 1950-2025
"""
    )


def test_get_euro2usd():

    key = datetime.datetime(2000, 1, 1)
    result = wb_data.get_euro2usd()[key]

    assert round(result, 1) == 1.1


def test_get_can2usd():

    key = datetime.datetime(2000, 1, 1)
    result = wb_data.get_can2usd()[key]

    assert round(result, 1) == 1.5


def test_get_gbp2usd():

    key = datetime.datetime(2000, 1, 1)
    result = wb_data.get_gbp2usd()[key]

    assert round(result, 1) == 0.7


def test_get_real_effective_exchange_index():

    result = wb_data.get_real_effective_exchange_index()
    result = result.loc[
        (result.iso_code == "FRA") & (result.year.dt.year == 2005), "value"
    ]

    assert round(result.sum(), 0) == 104
