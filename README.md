# pydeflate

[![pypi](https://img.shields.io/pypi/v/pydeflate.svg)](https://pypi.python.org/pypi/pydeflate)
[![Documentation Status](https://readthedocs.org/projects/pydeflate/badge/?version=latest)](https://pydeflate.readthedocs.io/en/latest/?version=latest)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Downloads](https://pepy.tech/badge/pydeflate/month)](https://pepy.tech/project/pydeflate)
[![Coverage](https://codecov.io/gh/jm-rivera/pydeflate/branch/main/graph/badge.svg?token=uwKI5DyO3w)](https://codecov.io/gh/jm-rivera/pydeflate)

**pydeflate** is a Python package to convert flows data to constant
prices. This can be done from any source currency to any desired base
year and currency. **Pydeflate** can also be used to convert constant
data to current prices and to convert from one currency to another (in
current and constant prices). Users can choose the source of the
exchange and deflator/prices data (currently, IMF, World Bank or OECD
DAC).

## Getting started

### Installation

pydeflate can be installed from PyPI. From the command line:

```bash

pip install pydeflate

```

## Basic usage

### Current to constant

Convert data expressed in current USD prices to constant EUR prices for
a given base year:

```python
from pydeflate import deflate, set_pydeflate_path
import pandas as pd

# Specify where the deflator and exchange data should be saved
set_pydeflate_path("path/to/data/folder")

# example data
data = {
    'iso_code': ['FRA', 'USA', 'GTM'],
    'year': [2017, 2017, 2017],
    'value': [50, 100, 200]
}

# create an example dataframe, in current USD prices
df = pd.DataFrame.from_dict(data)

# convert to EUR 2015 constant prices
df_constant = deflate(
    df=df,
    base_year=2015,
    deflator_source='world_bank',
    deflator_method='gdp',
    exchange_source="world_bank",
    source_currency="USA",  # since data is in USD
    target_currency="EMU",  # we want the result in constant EUR
    id_column="iso_code",
    id_type="ISO3",  # specifying this is optional in most cases
    date_column="year",
    source_column="value", # where the original data is
    target_col="value_constant", # where the new data will be stored
)
```

This results in a dataframe containing a new column `value_constant` in
2015 constant prices. In the background, pydeflate takes into account:

- changes in princes, through a gdp deflator in this case
- changes in exchange rates overtime

### Current Local Currency Units to constant in a different currency
Pydeflate can also handle data that is expressed in local currency
units. In that case, users can specify `LCU` as the source currency.

```python
from pydeflate import deflate, set_pydeflate_path
import pandas as pd

# Specify where the deflator and exchange data should be saved
set_pydeflate_path("path/to/data/folder")

# example data
data = {
    'country': ['United Kingdom', 'United Kingdom', 'Japan'],
    'date': [2011, 2015, 2015],
    'value': [100, 100, 100]
}

# create an example dataframe, in current local currency units
df = pd.DataFrame.from_dict(data)

# convert to USD 2018 constant prices
df_constant = deflate(
    df=df,
    base_year=2018,
    deflator_source='imf',
    deflator_method='pcpi',
    exchange_source="imf",
    source_currency="LCU",  # since data is in LCU
    target_currency="USA",  # to get data in USD
    id_column="iso_code",
    date_column="date",
    source_col="value",
    target_col="value",  # to not create a new column
)

```

### Constant to current
Users can also convert a dataset expressed in constant prices to current
prices using pydeflate. To avoid introducing errors, users should know
which methodology/ data was used to create constant prices by the
original source. The basic usage is the same as before, but the
`to_current` parameter is set to `True`.

For example, to convert DAC data expressed in 2016 USD constant prices
to current US dollars:

```python
from pydeflate import deflate, set_pydeflate_path
import pandas as pd

# Specify where the deflator and exchange data should be saved
set_pydeflate_path("path/to/data/folder")

# example data
data = {
    'dac_code': [302, 4, 4],
    'date': [2010, 2016, 2018],
    'value': [100, 100, 100]
}

# create an example dataframe, in current local currency units
df = pd.DataFrame.from_dict(data)

# convert to USD 2018 constant prices
df_current = deflate(
    df=df,
    base_year=2016,
    deflator_source='oecd_dac',
    deflator_method='dac_deflator',
    exchange_source="oecd_dac",
    source_currency="USA",  # since data is in USD constant
    target_currency="LCU",  # to get the current LCU figures
    id_column="dac_code",
    id_type="DAC",
    date_column="date",
    source_column="value",
    target_column="value_current",
    to_current=True,
)
```

## Data source and method options

In order to convert the data, pydeflate uses data on **price/gdp deflators** and
**exchange rates**. Each of these data sources can come from the `OECD DAC`,
`IMF (WEO)` or `World Bank`.

For all sources, Exchange rates between two non USD currency pairs are derived from
the LCU to USD exchange rates selected.

### International Monetary Fund World Economic Outlook ("imf")

For price/gdp deflators from the IMF, the following options are available (`deflator_method`):
- `gdp`: in order to use GDP deflators.
- `pcpi`: in order to use Consumer Price Index data.
- `pcpie`: to use end-of-period Consumer Price Index data
  (e.g. for December each year).

The IMF provides estimates where data is not available, including for several
years into the future. Using these price deflators, combined with the corresponding
exchange rates, allows users to convert data to constant prices for future years.

For exchange rates, the following options are available from the imf (`exchange_method`):
- `implied`: to use the exchange rates used by the World Economic Outlook, derived from
    the WEOs data on GDP in US Dollars and Local Currency Units.

### World Bank ("world_bank")

For price/gdp deflators from the World Bank, the following options are available (`deflator_method`):


In terms of price or GDP deflators, pydeflate provides the following
- `gdp`: in order to use GDP deflators.
- `gdp_linked`: to use the World Bank's GDP deflator series which
  has been linked to produce a consistent time series to
  counteract breaks in series over time due to changes in base
  years, sources or methodologies.
- `cpi`: to use Consumer Price Index data

For exchange rates, the following options are available from the World Bank (`exchange_method`):
- `yearly_average`: as used by the World Bank, based on IMF International Financial Statistics data.


### OECD Development Assistance Committee ("oecd_dac")

For price/gdp deflators from the OECD DAC, the following options are available (`deflator_method`):

In terms of price or GDP deflators, pydeflate provides the following:
- `dac_deflator`: in order to use the DAC's own deflator series.

For exchange rates, the following options are available from the OECD DAC (`exchange_method`):
- `implied`: to use the exchange rates used and published by the DAC.



## Additional features

Pydeflate relies on data from the World Bank, IMF and OECD for its
calculations. This data is updated periodically. If the version of the
data stored in the user's computer is older than 50 days, pydeflate will
show a warning on import.

Users can always update the underlying data by using:

```python
import pydeflate

pydeflate.update_all_data()

```

Pydeflate also provides users with a tool to exchange figures from one
currency to another, without applying any deflators. This should only be
used on numbers expressed in current prices, however.

For example, to convert numbers in current Local Currency Units (LCU) to
current Canadian Dollars:

```python
import pydeflate
import pandas as pd

# example data
data = {
    'iso_code': ['GBR', 'CAN', 'JPN'],
    'date': [2011, 2015, 2015],
    'value': [100, 100, 100]
}

# create an example dataframe, in current local currency units
df = pd.DataFrame.from_dict(data)

# convert to USD 2018 constant prices
df_can = pydeflate.exchange(
    df=df,
    source_currency="LCU",  # since data is in LCU
    target_currency="CAN",  # to get data in Canadian Dollars
    rates_source='imf', 
    value_column='value',
    target_column='value_CAN',
    id_column="iso_code",
    id_type="ISO3",
    date_column="date",
)

```

### Credits

This package relies on data from the following sources:

- OECD DAC: <https://www.oecd.org/dac/> (Official Development
  assistance data (DAC1), DAC deflators, and exchange rates used by
  the DAC)
- IMF World Economic Outlook:
  <https://www.imf.org/en/Publications/WEO> (GDP and price deflators)
- World Bank DataBank: <https://databank.worldbank.org/home.aspx>
  (exchange rates, GDP and price deflators)

This data is provided based on the terms and conditions set by the
original sources.