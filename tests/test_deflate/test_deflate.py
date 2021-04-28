#!/usr/bin/env python

"""Tests for `pydeflate` package."""

import pytest
import pandas as pd


from pydeflate.deflate import deflate


def dummy_data():
    
    """Data for South Africa taken from World Bank"""
    
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
    
    return df

def test_deflate_data():
    
    df = dummy_data()
    
    df2c = deflate.deflate_data(df, method='gdp_ratio', base=2010,
                                value_column='gdp_current')
    
    df2c['difference'] = abs(100*((df2c.gdp_constant - df2c.value_constant)/df2c.gdp_constant))
    
    assert round(df2c.difference.mean(),1) <0.1
    
  