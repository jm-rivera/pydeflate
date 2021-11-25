#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 20 12:17:49 2021

@author: jorge
"""

import pytest

from pydeflate.get_data import oecd_data


def test__update_dac1():

    """Capture print statements which are only printed if download successful"""

    oecd_data._update_dac1()

    assert True


def test__update_dac_deflators():
    """Capture print statements which are only printed if successful"""

    oecd_data._update_dac_deflators()

    assert True


def test__update_dac_exchange():
    """Capture print statements which are only printed if successful"""

    oecd_data._update_dac_exchange()

    assert True


def test__get_zip_error():
    with pytest.raises(ConnectionError):
        oecd_data._get_zip("fake_url")


def test_get_xe_deflator_error():
    with pytest.raises(ValueError):
        oecd_data.get_xe_deflator("fake_currency")
