# Getting Started

This guide walks you through setting up pydeflate and understanding the basic workflow.

## Installation

Install pydeflate via pip:

```bash
pip install pydeflate --upgrade
```

## Initial Setup

Before using pydeflate, specify where deflator and exchange rate data should be cached. This needs to be done once per script or session.

```python
from pydeflate import set_pydeflate_path

# Set cache directory
set_pydeflate_path("path/to/data/folder")
```

!!! tip "Cache Location"
    Choose a persistent location for your cache directory. pydeflate will download data from external sources (IMF, World Bank, OECD) and store it here for reuse. This avoids repeated downloads and improves performance.

### Alternative: Environment Variable

You can also set the cache directory using an environment variable:

```bash
export PYDEFLATE_DATA_DIR="/path/to/data/folder"
```

Then you don't need to call `set_pydeflate_path()` in your code.

## DataFrame Requirements

pydeflate works with pandas DataFrames. Your DataFrame must contain at least three columns:

### 1. ID Column (Country Identifier)

By default, pydeflate expects **ISO3 country codes** (e.g., `USA`, `FRA`, `GBR`).

```python
import pandas as pd

data = {
    'country': ['USA', 'FRA', 'JPN'],  # ISO3 codes
    'year': [2015, 2016, 2017],
    'amount': [100, 200, 300]
}
df = pd.DataFrame(data)
```

!!! info "Converting to ISO3 Codes"
    If your data uses different country identifiers (names, ISO2 codes, etc.), convert them to ISO3 before using pydeflate. Recommended libraries:

    - [`bblocks-place`](https://github.com/ONEcampaign/bblocks-places)
    - [`hdx-python-country`](https://github.com/OCHA-DAP/hdx-python-country)

#### Using Source-Specific Codes

If your data uses codes from the same source you're querying (e.g., DAC codes, IMF entity codes), set `use_source_codes=True`:

```python
# Data with DAC codes
data = {
    'dac_code': [4, 302, 12],
    'year': [2015, 2016, 2017],
    'amount': [100, 200, 300]
}
df = pd.DataFrame(data)

# Use DAC codes directly
result = oecd_dac_deflate(
    data=df,
    base_year=2015,
    id_column="dac_code",
    use_source_codes=True,  # Enable source codes
    ...
)
```

### 2. Year Column

Can be a string, integer, or datetime. By default, pydeflate looks for a column named `year`.

```python
# All these formats work:
df['year'] = [2015, 2016, 2017]                    # Integer
df['year'] = ['2015', '2016', '2017']              # String
df['year'] = pd.to_datetime(['2015', '2016', '2017'])  # Datetime
```

If your year column has a different name, specify it:

```python
result = imf_gdp_deflate(
    data=df,
    year_column="fiscal_year",  # Custom column name
    ...
)
```

#### Custom Year Formats

For non-standard formats, provide a `year_format` string:

```python
# Financial year format: "FY2015"
result = imf_gdp_deflate(
    data=df,
    year_column="fiscal_year",
    year_format="FY%Y",
    ...
)
```

### 3. Value Column

The numeric column to convert. By default, pydeflate looks for a column named `value`.

```python
data = {
    'country': ['USA', 'FRA'],
    'year': [2015, 2016],
    'value': [100.5, 200.75]  # Must be numeric (int or float)
}
```

Specify a different column name if needed:

```python
result = imf_gdp_deflate(
    data=df,
    value_column="gdp_usd",  # Custom column name
    ...
)
```

## Basic Workflow

### Step 1: Import and Setup

```python
from pydeflate import imf_gdp_deflate, set_pydeflate_path
import pandas as pd

# Set cache directory
set_pydeflate_path("./pydeflate_data")
```

### Step 2: Prepare Your Data

```python
# Create or load your DataFrame
data = {
    'iso_code': ['USA', 'GBR', 'JPN'],
    'year': [2017, 2018, 2019],
    'value': [1000, 2000, 3000]
}
df = pd.DataFrame(data)
```

### Step 3: Convert Prices

```python
# Convert from current USD to constant 2015 EUR
result = imf_gdp_deflate(
    data=df,
    base_year=2015,                     # Year for constant prices
    source_currency="USA",              # Current currency (USD)
    target_currency="FRA",              # Target currency (EUR)
    id_column="iso_code",               # Country identifier column
    year_column="year",                 # Year column
    value_column="value",               # Value column to convert
    target_value_column="value_2015"    # New column for results
)

print(result)
```

The result includes your original columns plus the new `value_2015` column with converted values.

## Common Parameters

All deflation and exchange functions share these parameters:

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `data` | Yes | - | pandas DataFrame to convert |
| `id_column` | Yes | - | Column with country identifiers (ISO3 by default) |
| `year_column` | No | `"year"` | Column with year values |
| `value_column` | No | `"value"` | Column with values to convert |
| `target_value_column` | No | Same as `value_column` | Column name for results |
| `source_currency` | Yes* | - | Source currency (ISO3 country code or `"LCU"`) |
| `target_currency` | Yes* | - | Target currency (ISO3 country code or `"LCU"`) |
| `base_year` | Yes** | - | Base year for constant prices |
| `use_source_codes` | No | `False` | Use source-specific country codes |
| `update` | No | `False` | Force update of cached data |

\* Required for exchange and deflation functions
\*\* Required for deflation functions

## Currency Codes

pydeflate accepts both country codes and common currency abbreviations:

```python
# These are equivalent:
source_currency="USA"  # ISO3 country code
source_currency="USD"  # Currency abbreviation

target_currency="FRA"  # For Eurozone countries
target_currency="EUR"  # Convenience mapping

# Other supported abbreviations:
"GBP" → "GBR"  # British Pound
"JPY" → "JPN"  # Japanese Yen
"CAD" → "CAN"  # Canadian Dollar
```

### Local Currency Units (LCU)

Use `"LCU"` to work with each country's local currency:

```python
# Convert from local currencies to USD
imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="LCU",  # Each country's local currency
    target_currency="USA",
    ...
)
```

## Data Updates

pydeflate caches downloaded data locally. If cached data is older than 50 days, you'll see a warning:

```
Warning: Cached data is 65 days old. Consider updating with update=True
```

To force an update:

```python
result = imf_gdp_deflate(
    data=df,
    base_year=2015,
    update=True,  # Download fresh data
    ...
)
```

## Next Steps

Now that you understand the basics, explore specific use cases:

- [**Deflation Guide**](deflate.md) - Detailed examples for all deflation methods
- [**Currency Exchange**](exchange.md) - Currency conversion without deflation
- [**Data Sources**](data-sources.md) - Choosing between IMF, World Bank, and OECD DAC

## Quick Reference

```python
# Deflation functions
from pydeflate import (
    imf_gdp_deflate,      # IMF GDP deflator
    imf_cpi_deflate,      # IMF CPI (period average)
    imf_cpi_e_deflate,    # IMF CPI (end-of-period)
    wb_gdp_deflate,       # World Bank GDP deflator
    wb_gdp_linked_deflate,# World Bank linked GDP deflator
    wb_cpi_deflate,       # World Bank CPI
    oecd_dac_deflate,     # OECD DAC deflator
)

# Exchange functions
from pydeflate import (
    imf_exchange,         # IMF exchange rates
    wb_exchange,          # World Bank exchange rates
    wb_exchange_ppp,      # World Bank PPP exchange rates
    oecd_dac_exchange,    # OECD DAC exchange rates
)

# Configuration
from pydeflate import set_pydeflate_path
```
