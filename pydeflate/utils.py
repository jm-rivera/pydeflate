#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 13:07:16 2021

@author: jorge
"""

# %% Import required packages and create paths
import pandas as pd
import wbgapi as wb
import os


path = os.path.dirname(__file__)
ppath = os.path.dirname(path)


# %% update data

def update_exchange(test=False):

    try:

        e = wb.data.DataFrame('PA.NUS.FCRF', mrv=25, numericTimeKeys=True, labels=False,
                              columns='series', timeColumns=True).reset_index()

    except:
        raise ConnectionError(
            'Failed to retreive data from WorldBank. Try again or use update=False')

    e = e.rename(columns={'economy': 'iso_code',
                          'PA.NUS.FCRF': 'value',
                          'time': 'year'})

    e = e.dropna(subset=['value'])

    e.to_csv(path+r'/data/exchange_data.csv', index=False)
    print('Updated exchange data')
    if test:
        return e


def update_gdp(test=False):
    try:
        gdp_lcu = wb.data.DataFrame('NY.GDP.MKTP.CN', mrv=25, numericTimeKeys=True, labels=False,
                                    columns='series', timeColumns=True).reset_index()

        gdp_const = wb.data.DataFrame('NY.GDP.MKTP.KD', mrv=25, numericTimeKeys=True, labels=False,
                                      columns='series', timeColumns=True).reset_index()

    except:
        raise ConnectionError(
            'Failed to retreive data from WorldBank. Try again or use update=False')

    gdp_lcu = gdp_lcu.rename(columns={'economy': 'iso_code',
                                      'NY.GDP.MKTP.CN': 'value',
                                      'time': 'year'})

    gdp_const = gdp_const.rename(columns={'economy': 'iso_code',
                                          'NY.GDP.MKTP.KD': 'value',
                                          'time': 'year'})

    gdp_lcu.to_csv(path+r'/data/gdp_lcu_raw.csv', index=False)
    gdp_const.to_csv(path+r'/data/gdp_const_raw.csv', index=False)

    print('Updated GDP data')
    if test:
        return gdp_lcu, gdp_const


def update_data(indicators=['xe', 'gdp']):

    # Exchange rate data
    indicators_dict = {'xe': update_exchange, 'gdp': update_gdp}

    if isinstance(indicators, str):
        if indicators == 'all':
            _, _ = update_exchange(), update_gdp()
        else:
            raise ValueError(f'"{indicators}" is not valid. Indicators must be a list of valid indicators, or \
                             the string "all" to update all indicators at once')

    elif isinstance(indicators, list):

        for i in indicators:
            if i not in indicators_dict.keys():
                raise ValueError(f'Invalid indicator {i}')
            indicators_dict[i]()

    else:
        raise TypeError(
            f'Indicators list is of an invalid type "{type(indicators)}"')


# %%

def clean_df(df, country_column, year_column):
    """Rename/clean df to match provided data"""

    df.columns = [country_column, year_column, 'deflator']

    if df[year_column].dtype != 'datetime64[ns]':
        df[year_column] = pd.to_datetime(df[year_column], format='%Y')

    return df


def exchange_rates():
    """
    Gets exchange rates from the World Bank (indicator PA.NUS.FCRF) for the last
    25 non-empty values for all countries.


    Returns
    -------
    A Pandas DataFrame
        Containing 3 columns: iso_code, year, and value (the exchange rates).

    """

    return pd.read_csv(path+r'/data/exchange_data.csv')


def country_rebase(df: pd.DataFrame, c: str, base: int = 2019,
                   value_column='value', year_column='year') -> pd.DataFrame:
    """ Function used to rebase deflators or exchange rates.

        It should be applied to a dataframe, and the country name must be 
        passed individually as a string.

        The base year can be optionall defined (2019 is default)"""

    # Error handling
    if type(base) != int:
        raise ValueError('The base year must be passed as an integer')

    if type(df) != pd.DataFrame:
        raise TypeError('A DataFrame must be provided')

    if df[year_column].dtype == 'datetime64[ns]':
        df[year_column] = df[year_column].dt.year
        year_is_date = True

    # Filter the dataframe to keep only the selected country
    country = df.loc[df.iso_code == c].reset_index(drop=True)

    # Convert the year column to integer
    country[year_column] = country[year_column].astype(int)

    # Try to create a variable containing the value for the base year. If base
    # Year is unavailable, an error will be printed but script will continue
    try:
        base = float(country.loc[country[year_column]
                                 == base, value_column].values)
    except:
        pass

    country['deflator'] = 100*(country[value_column] / base)

    try:
        if year_is_date:
            country[year_column] = pd.to_datetime(
                country[year_column], format='%Y')
    except:
        pass

    return country[['iso_code', year_column, 'deflator']]


def gdp_deflator(base: int = 2019) -> pd.DataFrame:
    """Return gdp deflators per country per year"""

    # Read the deflators data. Some cleaning done manually before
    df = pd.read_csv(path+r'/data/deflators_data.csv')

    # Melt dataframe
    df = df.melt(id_vars='iso_code', var_name='year')

    # Remove number formatting
    df.value = df.value.str.replace(',', '')

    # Change number type to float
    df.value = df.value.astype(float)

    # Check if selected base year is available in the data
    if base not in list(set(df.year.astype(int))):
        raise ValueError(
            f'The base year provided "{base}" is not available in the data')

    # Create a country name set
    countries = list(set(df.iso_code))

    # Return dataframe with all countries rebased
    return pd.concat([country_rebase(df, c, base=base) for c in countries], ignore_index=True)


def exchange_deflator(base: int = 2019) -> pd.DataFrame:
    """Return exchange deflators per country per year."""

    # Using the wb data api, get foreign exchange data
    e = exchange_rates()

    countries = list(set(e.iso_code))

    return pd.concat([country_rebase(e, c, base=base) for c in countries], ignore_index=True)


def gdp_xe_deflator(base: int = 2019):

    # Import and format gdp data
    gdp_def_data = gdp_deflator(base=base)

    # Import and format exchange data
    xe_def_data = exchange_deflator(base=base)

    # Create deflators dataframe
    dft = gdp_def_data.merge(xe_def_data, on=['iso_code', 'year'], how='inner',
                             suffixes=('_gdp', '_currency'))

    # Create combined deflator
    dft['deflator'] = dft.deflator_gdp/dft.deflator_currency

    return dft[['iso_code', 'year', 'deflator']].reset_index(drop=True)


def gdp_factor(year: int = 2010, output_type: str = 'usd', output_base=2010) -> pd.DataFrame:
    """
    Calculates a gdp deflator factor, sometimes used to convert LCU into constant USD.
    For example, ReSAKKS calculates this factor by dividing current LCU GDP by constant USD GDP.

    This script returns the LCU-USD Constant conversion factor, or the equivalent factor
    for converting current USD into Constant USD.

    Parameters
    ----------
    year : int, optional
        The base year used by the World Bank for its constant GDP numbers. The default is 2010.
    output_type : str, optional
        Selects whether output can be applied to convert constant usd to current usd ('usd')
        or to convert usd to current LCU ('lcu'). The default is 'usd'.
    update : bool, optional
        Whether to update the underlying WB GDP data. The default is False.

    Raises
    ------
    ValueError
        A value error is raised if the output type is incorrectly specified.

    Returns
    -------
    Pandas DataFrame
        The output of this function is a Pandas DataFrame containing only 3 
        columns: iso_code (str), year (datetime), and factor (float).

    """
    # Error handling
    if output_type not in ['usd', 'lcu']:
        raise ValueError(f'{output_type} must be "usd" or "lcu"')

    gdp_lcu = pd.read_csv(path+r'/data/gdp_lcu_raw.csv')
    gdp_const = pd.read_csv(
        path+r'/data/gdp_const_raw.csv')

    # Merge gdp in lcu and gdp in constant
    factor = gdp_lcu.merge(
        gdp_const, on=['iso_code', 'year'], suffixes=('_lcu', '_constant'))

    # Calculate factor
    factor['factor'] = factor.value_lcu/factor.value_constant

    if output_type == 'usd':
        # get exchange rates
        factor = factor.merge(exchange_rates(), on=[
                              'iso_code', 'year'], how='left')

        # correct exchange rates for ZWE which uses usd since 2009
        factor.loc[(factor.iso_code == 'ZWE') & (
            factor.year > 2008), 'value'] = 1

        # Produce usd factor. This means data in constant usd will be returned in current usd
        factor.factor = (factor.factor/factor.value)

    # Drop missing data
    factor = factor.dropna(subset=['factor'])

    countries = list(set(factor['iso_code']))

    factor = pd.concat([country_rebase(factor, c, base=output_base, value_column='factor') for c in countries],
                       ignore_index=True)

    factor.deflator = factor.deflator/100

    # Convert year to datetime
    factor.year = pd.to_datetime(factor.year, format='%Y')

    # keep only relevant variables
    return factor[['iso_code', 'year', 'deflator']].reset_index(drop=True)
