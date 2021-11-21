#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 20 13:33:16 2021

@author: jorge
"""


import sys
import io

from pydeflate.tools import update_data
from pydeflate.get_data.imf_data import _update_weo


def test_update_all_data():

    """Capture print statements which are only printed if download successful"""

    data = data = {"WEO data": _update_weo}

    try:
        update_data.update_all_data(data)
    except Exception:
        raise Exception("Test Failed")


def test_update_all_data_error():
    def __fake_func():
        raise ConnectionError("Could not download data")

    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    update_data.update_all_data({"fake_data": __fake_func})

    output = new_stdout.getvalue()

    sys.stdout = old_stdout

    print(output)

    assert output == "Could not download fake_data\n"
