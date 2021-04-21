#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 16:02:24 2021

@author: jorge
"""

# %% Import required packages and create paths
import pandas as pd

import os


path = os.path.dirname(__file__)
ppath = os.path.dirname(path)


from pydeflate.deflate import deflate_data

#%% South Africa

years = list(range(2008,2020))
gdp_current = [286.77, 295.936, 375.349, 416.419, 396.333,
               366.829, 350.905, 317.621, 296.357, 349.544,
               368.289, 351.432]

gdp_constant = [369.967, 364.276, 375.349, 387.677, 396.257,
                406.105, 413.606, 418.543, 420.213, 426.157,
                429.511, 430.167]

df = pd.DataFrame(list(zip(years, gdp_current, gdp_constant)), columns=['year',
                                                                        'gdp_current',
                                                                        'gdp_constant'])

df['iso_code'] = 'ZAF'
df = deflate_data(df,
                    method='gdp_ratio',
                    country_column='iso_code',
                    year_column = 'year',
                    value_column = 'gdp_current',
                    base = 2019,
                    to_current=False
                    )


