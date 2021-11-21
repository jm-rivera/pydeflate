#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 20 12:17:49 2021

@author: jorge
"""

import pytest

from pydeflate.get_data import oecd_data
import sys
import io


def test__update_dac1():

    """Capture print statements which are only printed if download successful"""

    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    oecd_data._update_dac1()

    output = new_stdout.getvalue()

    sys.stdout = old_stdout

    print(output)

    assert (
        output
        == """Downloading DAC1 data, which may take a bit
Sucessfully downloaded DAC1 data
"""
    )


def test__update_dac_deflators():
    """Capture print statements which are only printed if successful"""

    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    oecd_data._update_dac_deflators()

    output = new_stdout.getvalue()

    sys.stdout = old_stdout

    print(output)

    assert output == """Updated OECD DAC deflators 2019\n"""


def test__update_dac_exchange():
    """Capture print statements which are only printed if successful"""

    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    oecd_data._update_dac_exchange()

    output = new_stdout.getvalue()

    sys.stdout = old_stdout

    print(output)

    assert output == """Updated OECD DAC exchange rates\n"""


def test__get_zip_error():
    with pytest.raises(ConnectionError):
        oecd_data._get_zip("fake_url")


def test_get_xe_deflator_error():
    with pytest.raises(ValueError):
        oecd_data.get_xe_deflator("fake_currency")
