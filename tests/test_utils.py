#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 26 19:33:55 2021

@author: jorge
"""


from pydeflate.utils import warn_updates
import json

from pydeflate.config import paths

import pytest


def test_warn_updates():
    with open(paths.data + r'/data_updates.json') as file:
        updates = json.load(file)

    updates['test'] = '2020-01-01'

    with open(paths.data + r'/data_updates.json', "w") as outfile:
        json.dump(updates, outfile)

    with pytest.warns(UserWarning):
        warn_updates()

    with open(paths.data + r'/data_updates.json') as file:
        updates = json.load(file)

    _ = updates.pop('test')

    with open(paths.data + r'/data_updates.json', "w") as outfile:
        json.dump(updates, outfile)