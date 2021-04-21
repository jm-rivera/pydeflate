#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 13:06:41 2021

@author: jorge
"""

# %% Import required packages and create paths
import pydeflate.utils as utils
import pandas as pd
import os


path = os.path.dirname(__file__)
ppath = os.path.dirname(path)


# %%

def deflate_data(df: pd.DataFrame, method: str = 'gdp_xe', country_column: str = 'iso_code', year_column: str = 'year',
                 value_column: str = 'value', base: int = 2019, to_current: bool = False) -> pd.DataFrame:
    """
    Converts a column in a pandas dataframe to constant prices or vice-versa. 
    Two methods are posible at present: 
        - 'gdp_xe', which creates a common unit of measurement, taking into account changes
        in prices (GDP deflators) and changes in exchange rates over time, for each
        country. Data passed must be passed in current prices unless "to_current" is true.

        - 'gdp_ratio', which uses a GDP ratio approach, where a factor is applied to 
        the LCU data to transform it to constant prices. This factor is obtained by dividing
        GDP LCU current by GDP USD Constant. Data passed must be passed in current prices
        unless "to_current" is true.



    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame, tidy-long, with iso3 codes to identify countries, and years as int or datetime.
    method : str, optional
        Currently two methodologies are accepted: 'gdp_xe' or 'gdp_ratio'. The default is 'gdp_xe'.
    country_column : str, optional
        The column containing iso3 codes. The default is iso_code.
    year_column : str, optional
        The column containing the years. The default is year.  
    value_column : str, optional
        The column containing the values to deflate. The default is value.
    base : int, optional
        The desired base year for the data. The default is 2019.
    to_current : bool, optional
        Whether to convert from constant to current instead of current to constant. The default is False.


    Returns
    -------
    Pandas DataFrame
        The original dataframe including an additional column called either 'value_current' or 
        'value_constant' depending on the type of operation performed.

    """

    # Error handling
    if country_column not in df.columns:
        raise ValueError(
            f'{country_column} not a valid column name for countries')

    if year_column not in df.columns:
        raise ValueError(f'{year_column} not a valid column name for years')

    if value_column not in df.columns:
        raise ValueError(f'{value_column} not a valid column name for values')

    if df[year_column].dtype not in [int, 'datetime64[ns]']:
        raise TypeError(
            'Years are not correctly formatted as integers or datetime objects')

    if df[value_column].dtype not in [int, float]:
        raise TypeError('Values must be integers or floats')

    if method not in ['gdp_xe', 'gdp_ratio']:
        raise TypeError(
            'A valid method must be selected: "gdp_xe" or "gdp_ratio".')

    # Convert year column to datetime if needed
    if df[year_column].dtype == int:
        date_int = True
        df[year_column] = pd.to_datetime(df[year_column], format='%Y')

    # Create right deflator

    if method == 'gdp_xe':
        deflator = utils.clean_df(utils.gdp_xe_deflator(base=base),
                                  country_column, year_column)

    elif method == 'gdp_ratio':
        deflator = utils.clean_df(utils.gdp_factor(output_type='usd', output_base=base),
                                  country_column, year_column)

    # Add deflator to provided data
    df = df.merge(deflator, on=[country_column, year_column], how='left')

    # Deflate values
    if to_current:
        df['value_current'] = df[value_column]*df['deflator']

    else:
        df['value_constant'] = df[value_column]/(df['deflator'])

    # drop deflator column
    df.drop('deflator', axis=1, inplace=True)

    # convert date column back to int if needed
    try:
        if date_int:
            df[year_column] = df[year_column].dt.year
    except:
        pass

    return df.reset_index(drop=True)
