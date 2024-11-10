# pydeflate

[![pypi](https://img.shields.io/pypi/v/pydeflate.svg)](https://pypi.python.org/pypi/pydeflate)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Downloads](https://pepy.tech/badge/pydeflate/month)](https://pepy.tech/project/pydeflate)

**pydeflate** is a Python package to:
- Convert current price data to constant prices.
- Convert constant price data to current prices.
- Convert data from one currency to another (in both current and constant prices).

When converting to or from constant prices, it takes into account changes in prices and exchange rates over time. This allows for accurate comparisons across years, countries, and currencies.

## Important Note

**pydeflate v2 has recently been released. It includes api changes which break backwards-compatibility**. While a version of the `deflate` function is still available, it is now deprecated and will be removed in future versions. Please use the new deflator functions for improved simplicity, clarity and performance.


# Table of Contents


- [Installation](#installation)

- [Basic Usage](#basic-usage)
  - [Setting Up pydeflate](#setting-up-pydeflate)
  - [DataFrame Requirements](#dataframe-requirements)
  
- [Converting Current to Constant Prices](#converting-current-to-constant-prices)
  - [Example](#example-convert-current-to-constant-prices)

- [Available Deflator Functions](#available-deflator-functions)

- [Currency Conversion](#currency-conversion)
  - [Example](#example-currency-conversion)

- [Example: Using Source-Specific Codes](#example-using-source-specific-codes)

- [Data Sources and Method Options](#data-sources-and-method-options)
  - [International Monetary Fund](#international-monetary-fund)
  - [World Bank](#world-bank)
  - [OECD Development Assistance Committee](#oecd-development-assistance-committee)
  - [Sources](#sources)

- [Handling Missing Data](#handling-missing-data)

- [Updating Underlying Data](#updating-underlying-data)

## Installation

Install pydeflate using pip:

```bash
pip install pydeflate --upgrade
```

## Basic Usage

### Setting Up pydeflate

Before using pydeflate, you must specify where the deflator and exchange data should be saved. This only needs to be done once per script or notebook.

```python
from pydeflate import set_pydeflate_path

# Specify the path where deflator and exchange data will be saved
set_pydeflate_path("path/to/data/folder")
```

### DataFrame requirements
You need to provide a pandas DataFrame in order to convert data with `pydeflate`. The DataFrame must have at least the following columns:
- **An `id_column`**: you must specify its name using the `id_column` parameter. By default, it expects `ISO3` country codes. Previous versions of pydeflate used to convert data automatically, but that could inadvertently introduce errors by mis-identifying countries. You can use tools like `bblocks`, `hdx-python-country` or `country-converter` to help you add `ISO3` codes to your data. If you're working with data from the same source as the one you're using in `pydeflate`, you can also set `use_source_codes=True`. That allows you to use the same encoding as the source data (e.g., DAC codes, IMF entity codes).
- **A `year_column`**: which can be a string, integer, or datetime. This is needed in order to match the data to the right deflator or exchange rate. By default, pydeflate assumes that the year column is named `year`. You can change this by setting the `year_column` parameter. If the optional parameter `year_format` is not set, pydeflate will try to infer the format of the year column. You can also provide a `year_format` as a string, to specify the format of your data's year column.
- **A `value_column`**: which contains the data to be converted. By default, pydeflate assumes that the value column is named `value`. You can change this by setting the `value_column` parameter. The type of the value column must be numeric (int, float).

## Converting Current to Constant Prices

Pydeflate includes multiple sources and methods to deflate data. They all work in a very similar way. For this example, we will use the IMF GDP deflator and exchange rates data.

### Example: Convert Current to Constant Prices
In this example, we first import the `imf_gdp_deflate` function and create a sample DataFrame. We then convert the data to constant 2015 EUR prices using the IMF GDP deflators and exchange rates.

Note that both the `source_currency` and the `target_currency` are specified using the ISO3 country codes of the country whose currency is being used. Note that either can also be specified as `LCU` which stands for 'local currency units', or the local currency for each individual country, instead applying a single currency to all values. For convenience `pydeflate` also accepts the currency codes of certain countries (like `USD` in place of `USA`, `EUR` in place of any country that uses the euro, `GBP` in place of `GBR`, etc).

If the required data to perform the conversion is not available, pydeflate will download it from the source and save it in the specified data folder. If the stored data is older than 50 days, `pydeflate` will inform you and encourage you to set the `update_data` parameter to `True`.

```python
from pydeflate import imf_gdp_deflate, set_pydeflate_path
import pandas as pd

# Specify the path where deflator and exchange data will be saved
set_pydeflate_path("path/to/data/folder")

# Example data in current USD prices
data = {
    'iso_code': ['FRA', 'USA', 'GTM'],
    'year': [2017, 2017, 2017],
    'value': [50, 100, 200]
}

df = pd.DataFrame(data)

# Convert to constant EUR prices (base year 2015)
df_constant = imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="USA",  # Data is in USD
    target_currency="FRA",  # Convert to Euro
    id_column="iso_code", # must be ISO3 code
    year_column="year", # Can be string, integer or datetime
    value_column="value", # Column to be converted
    target_value_column="value_constant" # It could also be the same as value_column
)
```

### Available Deflator Functions

- `imf_gdp_deflate`: Uses GDP deflators and exchange rates from the IMF World Economic Outlook.
- `imf_cpi_deflate`: Uses Consumer Price Index and exchange rates data from the IMF World Economic Outlook.
- `imf_cpi_e_deflate`: Uses end-of-period Consumer Price Index and exchange rates data from the IMF World Economic Outlook.
- `wb_gdp_deflate`: Uses GDP deflators and exchange rates from the World Bank.
- `wb_gdp_linked_deflate`: Uses the World Bank’s linked GDP deflator and exchange rates data.
- `wb_cpi_deflate`: Uses Consumer Price Index and exchange rate data from the World Bank.
- `oecd_dac_deflate`: Uses the OECD DAC deflator series (prices and exchange rates).



## Currency Conversion
Pydeflate includes multiple sources for currency exchange. They all work in a very similar way, using yearly exchange rates. For this example, we will use the OECD DAC exchange rates.

### Example: Currency Conversion

```python
from pydeflate import oecd_dac_exchange, set_pydeflate_path
import pandas as pd

# Specify the path where deflator and exchange data will be saved
set_pydeflate_path("path/to/data/folder")

# Example data in current local currency units
data = {
    'iso_code': ['GBR', 'CAN', 'JPN'],
    'year': [2011, 2015, 2015],
    'value': [100, 100, 100]
}

df = pd.DataFrame(data)

# Convert from local currency (e.g GBP, CAD, JPY in this case) to Canadian Dollars
df_can = oecd_dac_exchange(
    data=df,
    source_currency="LCU", # Local currency units
    target_currency="CAN", # Convert to Canadian Dollars (can also use 'CAD')
    id_column="iso_code", # must be ISO3 code
    year_column="year", # Can be string, integer or datetime
    value_column="value", # Column to be converted
    target_value_column="value_can" # It could also be the same as value_column
)
```

## Example: Using Source-Specific Codes

If your data uses source-specific country codes (e.g., DAC codes), set use_source_codes=True and specify the appropriate id_column.

```python
from pydeflate import oecd_dac_deflate, set_pydeflate_path
import pandas as pd


# Specify the path where deflator and exchange data will be saved
set_pydeflate_path("path/to/data/folder")

# Example data with DAC codes
data = {
    'dac_code': [302, 4, 4],
    'year': [2010, 2016, 2018],
    'value': [100, 100, 100]
}

df = pd.DataFrame(data)

# Convert using DAC deflators and DAC codes
df_constant = oecd_dac_deflate(
    data=df,
    base_year=2016,
    source_currency="USA", # Data is in USD
    target_currency="LCU", # Convert to local currency units
    id_column="dac_code", # DAC codes
    use_source_codes=True,  # Use source-specific codes
    year_column="year", # Can be string, integer or datetime
    value_column="value", # Column to be converted
    target_value_column="value_constant" # It could also be the same as value_column
)

```

## Data Sources and Method Options

Pydeflate uses data on price/gdp deflators and exchange rates from various sources. Each source offers different options for deflators and exchange rates.

For all sources, Exchange rates between two non USD currency pairs are derived from
the LCU to USD exchange rates selected.

### International Monetary Fund
The IMF provides estimates where data is not available, including for several
years into the future. Using these price deflators, combined with the corresponding
exchange rates, can also allow users to convert data to constant prices for future years.

Deflator Functions:
- `imf_gdp_deflate`: Uses GDP deflators.
- `imf_cpi_deflate`: Uses Consumer Price Index data.
- `imf_cpi_e_deflate`: Uses end-of-period Consumer Price Index data.


Exchange Function:
- `imf_exchange`: Uses exchange rates derived from the IMF’s data.

Notes:
- IMF data includes estimates for future years, allowing conversion to constant prices for future dates.
- Exchange rates are derived from the IMF’s implied rates.

### World Bank

Deflator Functions:
- `wb_gdp_deflate`: Uses GDP deflators.
- `wb_gdp_linked_deflate`: Uses the World Bank’s linked GDP deflator series.
- `wb_cpi_deflate`: Uses Consumer Price Index data.

Exchange Function:
- `wb_exchange`: Uses yearly average exchange rates.

Notes:
- The linked GDP deflator series counters breaks in series over time due to changes in base years or methodologies.
- Exchange rates are based on IMF International Financial Statistics data

### OECD Development Assistance Committee

Deflator Function:
- `oecd_dac_deflate`: Uses the DAC’s own deflator series.

Exchange Function:
- `oecd_dac_exchange`: Uses exchange rates used and published by the DAC.

### Sources
This package relies on data from the following sources:
- OECD DAC: https://www.oecd.org/dac/
- IMF World Economic Outlook: https://www.imf.org/en/Publications/WEO
- World Bank DataBank: https://databank.worldbank.org/home.aspx

This data is provided based on the terms and conditions set by the
original sources.

## Handling Missing Data

Pydeflate relies on data from external sources. If there are missing values in the deflator or exchange rate data for certain countries or years, pydeflate will flag this in the output DataFrame. Ensure that your data aligns with the available data from the selected source.

## Updating Underlying Data

Pydeflate periodically updates its underlying data from the World Bank, IMF, and OECD. If the data on your system is older than 50 days, pydeflate will display a warning upon import.


