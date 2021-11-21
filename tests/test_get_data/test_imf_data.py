#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 20 12:18:13 2021

@author: jorge
"""


import pytest

from pydeflate.get_data import imf_data
from pydeflate import config
import sys
import io

import os


def test__update_weo():

    """Capture print statements which are only printed if download successful"""

    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    imf_data._update_weo(2020, 1)

    output = new_stdout.getvalue()

    sys.stdout = old_stdout

    print(output)

    assert output[-21:] == "2020-Apr WEO dataset\n"

    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    imf_data._update_weo(2020, 1)

    output = new_stdout.getvalue()

    sys.stdout = old_stdout

    print(output)

    assert output[0:7] == "Already"

    # cleaning
    file = config.paths.data + r"/weo2020_1.csv"

    if os.path.exists(file):
        os.remove(file)


def test_get_implied_ppp_rate():

    result = imf_data.get_implied_ppp_rate()

    result = result.loc[
        (result.iso_code == "GTM") & (result.year.dt.year == 1991), "value"
    ]

    assert round(result.sum(), 1) == 1.4
