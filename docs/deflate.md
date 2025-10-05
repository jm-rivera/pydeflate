# Usage Guide

This guide covers all deflation methods in pydeflate with practical examples. Deflation converts between current and constant prices, adjusting for inflation and exchange rate changes.

## Understanding price conversion

**Current prices** reflect the value at the time of measurement, including inflation.

**Constant prices** adjust values to a specific base year, removing inflation effects for accurate comparisons over time.

pydeflate handles both:

- **Current → Constant** (deflation): Remove inflation
- **Constant → Current** (inflation): Add inflation back

## IMF Deflators

The IMF World Economic Outlook provides GDP deflators and CPI data with estimates for future years.

### GDP Deflator (IMF)

Use GDP deflators when working with GDP or broad economic indicators.

```python
from pydeflate import imf_gdp_deflate, set_pydeflate_path
import pandas as pd

set_pydeflate_path("./pydeflate_data")

# Example: Convert GDP from current USD to constant 2015 USD
data = {
    'country': ['USA', 'GBR', 'JPN', 'FRA'],
    'year': [2017, 2018, 2019, 2020],
    'gdp': [19500, 2900, 4900, 2600]  # Billions, current USD
}
df = pd.DataFrame(data)

result = imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="USA",      # Current USD
    target_currency="USA",      # Constant USD (same currency)
    id_column="country",
    value_column="gdp",
    target_value_column="gdp_constant_2015"
)

print(result[['country', 'year', 'gdp', 'gdp_constant_2015']])
```

**When to use:**

- Analyzing GDP trends
- Comparing economic output over time
- Working with national accounts data

### CPI (Period Average)

Consumer Price Index measures changes in the price level of consumer goods and services.

```python
from pydeflate import imf_cpi_deflate

# Example: Adjust household expenditure for inflation
data = {
    'country': ['USA', 'GBR', 'DEU'],
    'year': [2018, 2019, 2020],
    'expenditure': [50000, 45000, 55000]  # Current prices
}
df = pd.DataFrame(data)

result = imf_cpi_deflate(
    data=df,
    base_year=2015,
    source_currency="LCU",      # Local currency
    target_currency="LCU",      # Keep in local currency
    id_column="country",
    value_column="expenditure",
    target_value_column="expenditure_2015"
)
```

**When to use:**

- Household expenditure analysis
- Wage comparisons
- Cost of living adjustments
- Consumer-focused metrics

### CPI (End-of-Period)

End-of-period CPI uses December values instead of annual averages.

```python
from pydeflate import imf_cpi_e_deflate

# Example: Adjust financial data using end-of-period CPI
data = {
    'country': ['USA', 'CAN'],
    'year': [2019, 2020],
    'revenue': [1000000, 1100000]
}
df = pd.DataFrame(data)

result = imf_cpi_e_deflate(
    data=df,
    base_year=2018,
    source_currency="USA",
    target_currency="USA",
    id_column="country",
    value_column="revenue",
    target_value_column="revenue_2018"
)
```

**When to use:**

- Financial reporting (December year-end)
- Comparing point-in-time values
- When data represents end-of-year snapshots

## World Bank Deflators

World Bank provides deflators derived from national accounts and IFS data.

### GDP Deflator (World Bank)

```python
from pydeflate import wb_gdp_deflate

# Example: Multi-country GDP comparison
data = {
    'iso3': ['BRA', 'IND', 'CHN', 'ZAF'],
    'year': [2015, 2016, 2017, 2018],
    'gdp_lcu': [6000, 153000, 82000, 4900]  # Local currency, billions
}
df = pd.DataFrame(data)

result = wb_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="LCU",      # Local currency
    target_currency="USA",      # Convert to USD
    id_column="iso3",
    value_column="gdp_lcu",
    target_value_column="gdp_usd_2015"
)

print(result[['iso3', 'year', 'gdp_lcu', 'gdp_usd_2015']])
```

### Linked GDP Deflator

The linked GDP deflator corrects for breaks in deflator series due to base year changes.

```python
from pydeflate import wb_gdp_linked_deflate

# Example: Long time-series analysis (1980-2020)
data = {
    'country': ['IND', 'IND', 'IND', 'IND'],
    'year': [1980, 1990, 2000, 2010],
    'investment': [100, 200, 400, 800]  # Current LCU
}
df = pd.DataFrame(data)

result = wb_gdp_linked_deflate(
    data=df,
    base_year=2010,
    source_currency="LCU",
    target_currency="LCU",
    id_column="country",
    value_column="investment",
    target_value_column="investment_2010"
)
```

**When to use:**

- Long time series (spanning multiple decades)
- Countries that frequently change base years
- Historical comparisons

!!! tip
    For time series spanning 20+ years, prefer `wb_gdp_linked_deflate` over `wb_gdp_deflate` to avoid breaks in the series.

### CPI (World Bank)

```python
from pydeflate import wb_cpi_deflate

# Example: Cross-country price comparison
data = {
    'country': ['KEN', 'UGA', 'TZA', 'RWA'],
    'year': [2018, 2018, 2019, 2019],
    'price_lcu': [100, 150, 120, 80]  # Local currency
}
df = pd.DataFrame(data)

result = wb_cpi_deflate(
    data=df,
    base_year=2015,
    source_currency="LCU",
    target_currency="USA",      # Convert to common currency
    id_column="country",
    value_column="price_lcu",
    target_value_column="price_usd_2015"
)
```

## OECD DAC Deflators

OECD DAC deflators are specifically designed for Official Development Assistance (ODA) and development finance.

### DAC Deflator

```python
from pydeflate import oecd_dac_deflate

# Example: Convert ODA from current to constant prices
data = {
    'donor': ['USA', 'GBR', 'FRA', 'DEU', 'JPN'],
    'year': [2015, 2016, 2017, 2018, 2019],
    'oda_usd': [30900, 18700, 11400, 25000, 15500]  # Current USD, millions
}
df = pd.DataFrame(data)

result = oecd_dac_deflate(
    data=df,
    base_year=2018,
    source_currency="USA",
    target_currency="USA",
    id_column="donor",
    value_column="oda_usd",
    target_value_column="oda_2018"
)

print(result[['donor', 'year', 'oda_usd', 'oda_2018']])
```

**When to use:**

- Official Development Assistance (ODA) analysis
- Development finance tracking
- Donor comparisons
- DAC reporting requirements

### Using DAC Codes

If your data uses DAC donor/recipient codes:

```python
# Data with DAC codes (not ISO3)
data = {
    'dac_code': [4, 12, 302, 701],  # USA=302, UK=12, France=4, etc.
    'year': [2015, 2016, 2017, 2018],
    'amount': [1000, 2000, 1500, 2500]
}
df = pd.DataFrame(data)

result = oecd_dac_deflate(
    data=df,
    base_year=2018,
    source_currency="USA",
    target_currency="USA",
    id_column="dac_code",
    use_source_codes=True,  # Important!
    value_column="amount",
    target_value_column="amount_2018"
)
```

## Converting Constant to Current

All deflation functions support reverse conversion (constant → current) using `to_current=True`.

```python
from pydeflate import imf_gdp_deflate

# Data already in constant 2015 prices
data = {
    'country': ['USA', 'GBR'],
    'year': [2018, 2019],
    'value_2015': [1000, 1100]  # Constant 2015 USD
}
df = pd.DataFrame(data)

# Convert back to current prices
result = imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="USA",
    target_currency="USA",
    id_column="country",
    value_column="value_2015",
    target_value_column="value_current",
    to_current=True  # Reverse operation
)

print(result[['country', 'year', 'value_2015', 'value_current']])
```

## Combining Deflation and Exchange

Convert both currency and price base in one operation:

```python
from pydeflate import imf_gdp_deflate

# Data in current local currency
data = {
    'country': ['JPN', 'GBR', 'AUS', 'CAN'],
    'year': [2017, 2018, 2019, 2020],
    'budget_lcu': [5000000, 800000, 150000, 200000]  # Millions LCU
}
df = pd.DataFrame(data)

# Convert to constant 2015 EUR
result = imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="LCU",      # From local currencies
    target_currency="FRA",      # To EUR
    id_column="country",
    value_column="budget_lcu",
    target_value_column="budget_eur_2015"
)

# Now all values are in constant 2015 EUR, comparable across countries and years
```

This is particularly useful for:

- Multi-country comparisons
- International development tracking
- Cross-border economic analysis

## Choosing a Deflator

| Use Case | Recommended Deflator |
|----------|---------------------|
| GDP, national accounts | `imf_gdp_deflate` or `wb_gdp_deflate` |
| Long time series (20+ years) | `wb_gdp_linked_deflate` |
| Consumer prices, wages | `imf_cpi_deflate` or `wb_cpi_deflate` |
| Year-end financial data | `imf_cpi_e_deflate` |
| Development assistance (ODA) | `oecd_dac_deflate` |
| Future year estimates | `imf_gdp_deflate` or `imf_cpi_deflate` |

## Complete Example

Here's a complete workflow for analyzing aid effectiveness:

```python
from pydeflate import oecd_dac_deflate, set_pydeflate_path
import pandas as pd

# Setup
set_pydeflate_path("./data")

# Load ODA data (example)
oda_data = {
    'donor': ['USA', 'GBR', 'FRA', 'DEU', 'JPN'] * 5,
    'year': sorted([2015, 2016, 2017, 2018, 2019] * 5),
    'oda_current_usd': [
        30900, 31000, 31500, 32000, 32500,
        18700, 19000, 19200, 19500, 19800,
        11400, 11600, 11800, 12000, 12200,
        25000, 25500, 26000, 26500, 27000,
        15500, 15800, 16000, 16200, 16500
    ]
}
df = pd.DataFrame(oda_data)

# Convert to constant 2018 USD for comparison
result = oecd_dac_deflate(
    data=df,
    base_year=2018,
    source_currency="USA",
    target_currency="USA",
    id_column="donor",
    value_column="oda_current_usd",
    target_value_column="oda_2018_usd"
)

# Calculate real growth
result = result.sort_values(['donor', 'year'])
result['growth'] = result.groupby('donor')['oda_2018_usd'].pct_change() * 100

print(result[['donor', 'year', 'oda_current_usd', 'oda_2018_usd', 'growth']])
```

## Getting Deflators Directly

**New in v2.3.0**: You can retrieve deflator data as DataFrames without providing your own data. This is useful for:

- Inspecting deflator values
- Analyzing deflator trends
- Pre-computing deflators for manual calculations
- Understanding how deflators change over time

### Basic Usage

```python
from pydeflate import get_imf_gdp_deflators, set_pydeflate_path

set_pydeflate_path("./data")

# Get deflators for specific countries and years
deflators = get_imf_gdp_deflators(
    base_year=2015,
    source_currency="USA",
    target_currency="EUR",
    countries=["USA", "FRA", "GBR"],  # Optional filter
    years=range(2010, 2024),  # Optional filter
)

# Returns DataFrame with: iso_code, year, deflator
print(deflators)
```

### Available Functions

All deflator functions have corresponding "get" versions:

- `get_imf_gdp_deflators()` - IMF GDP deflators
- `get_imf_cpi_deflators()` - IMF CPI deflators
- `get_imf_cpi_e_deflators()` - IMF end-of-period CPI deflators
- `get_wb_gdp_deflators()` - World Bank GDP deflators
- `get_wb_gdp_linked_deflators()` - World Bank linked GDP deflators
- `get_wb_cpi_deflators()` - World Bank CPI deflators
- `get_oecd_dac_deflators()` - OECD DAC deflators

### Inspecting Components

Use `include_components=True` to see how deflators are calculated:

```python
deflators = get_imf_gdp_deflators(
    base_year=2015,
    source_currency="USA",
    target_currency="EUR",
    countries=["USA"],
    include_components=True,  # Add component columns
)

# Returns: iso_code, year, deflator, price_deflator, exchange_deflator, exchange_rate
print(deflators)
```

The deflator is calculated as: `price_deflator / (exchange_deflator * exchange_rate)`

### Example: Analyzing Deflator Trends

```python
import matplotlib.pyplot as plt
from pydeflate import get_imf_gdp_deflators

# Get deflators for USA over time
deflators = get_imf_gdp_deflators(
    base_year=2015,
    countries=["USA"],
    years=range(2000, 2024)
)

# Plot the trend
plt.figure(figsize=(10, 6))
plt.plot(deflators["year"], deflators["deflator"], marker='o')
plt.title("US GDP Deflator Trend (Base Year 2015)")
plt.xlabel("Year")
plt.ylabel("Deflator")
plt.grid(True)
plt.show()
```

### Example: Manual Calculation

```python
from pydeflate import get_imf_gdp_deflators

# Get deflators
deflators = get_imf_gdp_deflators(
    base_year=2020,
    source_currency="USA",
    target_currency="USA"
)

# Manual deflation
my_value_2021 = 100  # USD in 2021
deflator_2021 = deflators[
    (deflators["iso_code"] == "USA") &
    (deflators["year"] == 2021)
]["deflator"].iloc[0]

constant_value = my_value_2021 / deflator_2021
print(f"${my_value_2021} in 2021 = ${constant_value:.2f} in constant 2020 USD")
```

## Next Steps

- [**Currency Exchange**](exchange.md) - Convert currencies without deflation
- [**Data Sources**](data-sources.md) - Detailed comparison of IMF, World Bank, and OECD
- [**Advanced Topics**](advanced/exceptions.md) - Error handling and advanced features
