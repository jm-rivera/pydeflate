# pydeflate

[![pypi](https://img.shields.io/pypi/v/pydeflate.svg)](https://pypi.python.org/pypi/pydeflate)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Downloads](https://pepy.tech/badge/pydeflate/month)](https://pepy.tech/project/pydeflate)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://jm-rivera.github.io/pydeflate/)

**pydeflate** is a Python package to:
- Convert current price data to constant prices.
- Convert constant price data to current prices.
- Convert data from one currency to another (in both current and constant prices).

When converting to or from constant prices, it takes into account changes in prices and exchange rates over time. This allows for accurate comparisons across years, countries, and currencies.

📚 **[Read the full documentation →](https://jm-rivera.github.io/pydeflate/)**

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

- [Getting Deflators and Exchange Rates Directly](#getting-deflators-and-exchange-rates-directly)
  - [Getting Deflators](#getting-deflators)
  - [Getting Exchange Rates](#getting-exchange-rates)
  - [Common Use Cases](#common-use-cases)

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

## Getting Deflators and Exchange Rates Directly

**New in v2.3.0**: You can now retrieve deflator and exchange rate data directly as DataFrames, without needing to provide your own data. This is useful for inspecting deflators, analyzing trends, or pre-computing values for later use.

### Getting Deflators

```python
from pydeflate import get_imf_gdp_deflators, set_pydeflate_path

# Specify the path where deflator data will be saved
set_pydeflate_path("path/to/data/folder")

# Get deflators for specific countries and years
deflators = get_imf_gdp_deflators(
    base_year=2015,
    source_currency="USA",
    target_currency="EUR",
    countries=["USA", "FRA", "GBR"],  # Optional: filter specific countries
    years=range(2010, 2024),  # Optional: filter specific years
)

# Returns a DataFrame with columns: iso_code, year, deflator
print(deflators.head())
```

You can also get the individual components that make up the deflator:

```python
# Include price deflator, exchange deflator, and exchange rate components
deflators_detailed = get_imf_gdp_deflators(
    base_year=2015,
    source_currency="USA",
    target_currency="EUR",
    include_components=True,  # Adds price_deflator, exchange_deflator, exchange_rate columns
)
```

### Available Get Deflator Functions

- `get_imf_gdp_deflators`: Get IMF GDP deflators
- `get_imf_cpi_deflators`: Get IMF CPI deflators
- `get_imf_cpi_e_deflators`: Get IMF end-of-period CPI deflators
- `get_wb_gdp_deflators`: Get World Bank GDP deflators
- `get_wb_gdp_linked_deflators`: Get World Bank linked GDP deflators
- `get_wb_cpi_deflators`: Get World Bank CPI deflators
- `get_oecd_dac_deflators`: Get OECD DAC deflators

### Getting Exchange Rates

```python
from pydeflate import get_imf_exchange_rates

# Get exchange rates for specific currency pairs
rates = get_imf_exchange_rates(
    source_currency="USD",
    target_currency="EUR",
    countries=["USA", "FRA", "GBR"],  # Optional: filter specific countries
    years=range(2010, 2024),  # Optional: filter specific years
)

# Returns a DataFrame with columns: iso_code, year, exchange_rate
print(rates.head())
```

### Available Get Exchange Rate Functions

- `get_imf_exchange_rates`: Get IMF exchange rates
- `get_wb_exchange_rates`: Get World Bank exchange rates
- `get_wb_ppp_rates`: Get World Bank PPP conversion rates
- `get_oecd_dac_exchange_rates`: Get OECD DAC exchange rates

### Common Use Cases

**Analyzing deflator trends:**
```python
import matplotlib.pyplot as plt

# Get US GDP deflators over time
deflators = get_imf_gdp_deflators(
    base_year=2015,
    countries=["USA"],
    years=range(2000, 2024)
)

plt.plot(deflators["year"], deflators["deflator"])
plt.title("US GDP Deflator (Base Year 2015)")
plt.show()
```

**Pre-computing deflators for manual calculations:**
```python
# Get deflators
deflators = get_imf_gdp_deflators(
    base_year=2020,
    source_currency="USA",
    target_currency="EUR"
)

# Use in your own calculations
my_value_2021 = 100  # USD in 2021
deflator_2021 = deflators[(deflators["iso_code"] == "USA") &
                          (deflators["year"] == 2021)]["deflator"].iloc[0]
constant_value = my_value_2021 / deflator_2021
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

## Advanced Features

### Error Handling

Pydeflate v2.1.3+ provides specific exception types for better error handling:

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import NetworkError, ConfigurationError, MissingDataError

try:
    result = imf_gdp_deflate(df, base_year=2015, source_currency="USA", target_currency="EUR")
except NetworkError as e:
    # Handle network failures (retry, fallback to cached data, etc.)
    print(f"Network error: {e}")
    # Implement retry logic
except ConfigurationError as e:
    # Handle invalid parameters (wrong currency codes, missing columns, etc.)
    print(f"Configuration error: {e}")
    raise
except MissingDataError as e:
    # Handle missing deflator/exchange data for specific country-year combinations
    print(f"Missing data: {e}")
    # Use alternative source or fill gaps
```

Available exception types:
- `PydeflateError`: Base exception for all pydeflate errors
- `NetworkError`: Network-related failures
- `ConfigurationError`: Invalid parameters or configuration
- `DataSourceError`: Issues loading or parsing data from sources
- `CacheError`: Cache operation failures
- `MissingDataError`: Required deflator/exchange data unavailable
- `SchemaValidationError`: Data validation failures

### Custom Data Sources (Plugin System)

You can register custom data sources without modifying pydeflate's code:

```python
from pydeflate.plugins import register_source, list_sources

# Define your custom source
@register_source("my_central_bank")
class MyCentralBankSource:
    def __init__(self, update: bool = False):
        self.name = "my_central_bank"
        self.data = self.load_my_data(update)  # Your data loading logic
        self._idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]

    def lcu_usd_exchange(self):
        # Return exchange rate data
        return self.data.filter(self._idx + ["pydeflate_EXCHANGE"])

    def price_deflator(self, kind="NGDP_D"):
        # Return deflator data
        return self.data.filter(self._idx + [f"pydeflate_{kind}"])

    def validate(self):
        # Validate data format
        if self.data.empty:
            raise ValueError("No data loaded")

# List all available sources
print(list_sources())  # ['DAC', 'IMF', 'World Bank', 'my_central_bank', ...]

# Your custom source is now available for use with pydeflate
```

### Advanced Configuration

For advanced use cases, you can use context managers to customize pydeflate's behavior:

```python
from pydeflate.context import pydeflate_session
import logging

# Use a custom cache directory and logging level
with pydeflate_session(data_dir="/tmp/my_cache", log_level=logging.DEBUG) as ctx:
    result = imf_gdp_deflate(df, base_year=2015, ...)
    # Data is cached in /tmp/my_cache
    # Debug logging is enabled

# Or set a default context for your entire application
from pydeflate.context import PydeflateContext, set_default_context

ctx = PydeflateContext.create(
    data_dir="/app/data/pydeflate_cache",
    log_level=logging.INFO
)
set_default_context(ctx)

# All subsequent pydeflate operations use this configuration
```

This is useful for:
- Using different cache directories for different projects
- Running multiple pydeflate operations in parallel without cache conflicts
- Customizing logging verbosity
- Testing with temporary cache directories

## Documentation

For comprehensive documentation including detailed examples, advanced features, and troubleshooting:

**[📚 Full Documentation](https://jm-rivera.github.io/pydeflate/)**

The documentation includes:
- [Getting Started Guide](https://jm-rivera.github.io/pydeflate/getting-started/) - Setup and DataFrame requirements
- [Deflation Guide](https://jm-rivera.github.io/pydeflate/deflation/) - All deflation methods with examples
- [Currency Exchange](https://jm-rivera.github.io/pydeflate/exchange/) - Currency conversion examples
- [Data Sources](https://jm-rivera.github.io/pydeflate/data-sources/) - IMF, World Bank, and OECD DAC comparison
- [Advanced Topics](https://jm-rivera.github.io/pydeflate/advanced/exceptions/) - Error handling, contexts, plugins, validation
- [Migration Guide](https://jm-rivera.github.io/pydeflate/migration/) - v1 to v2 migration
- [FAQ](https://jm-rivera.github.io/pydeflate/faq/) - Common questions and troubleshooting

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue on [GitHub](https://github.com/jm-rivera/pydeflate).

