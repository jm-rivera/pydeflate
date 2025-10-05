# Currency Exchange

This guide covers currency conversion using pydeflate's exchange rate functions. These functions convert values between currencies without adjusting for inflation.

## When to Use Exchange Functions

Use exchange functions when you need to:

- Convert between currencies at current prices (no inflation adjustment)
- Apply yearly average exchange rates
- Work with historical exchange rates from authoritative sources

For combined currency conversion + deflation, see the [Deflation Guide](deflate.md).

## IMF Exchange Rates

IMF exchange rates are derived from the World Economic Outlook database.

```python
from pydeflate import imf_exchange, set_pydeflate_path
import pandas as pd

set_pydeflate_path("./pydeflate_data")

# Example: Convert revenues from GBP to USD
data = {
    'country': ['GBR', 'GBR', 'GBR'],
    'year': [2015, 2016, 2017],
    'revenue_gbp': [1000, 1100, 1200]  # Current GBP
}
df = pd.DataFrame(data)

result = imf_exchange(
    data=df,
    source_currency="GBR",      # GBP
    target_currency="USA",      # USD
    id_column="country",
    value_column="revenue_gbp",
    target_value_column="revenue_usd"
)

print(result[['country', 'year', 'revenue_gbp', 'revenue_usd']])
```

### Features

- Yearly average exchange rates
- Includes future estimates (3-5 years ahead)
- Consistent with IMF WEO methodology

**When to use:**

- Economic analysis using IMF data
- Need future year estimates
- Consistency with IMF publications

## World Bank Exchange Rates

World Bank exchange rates are based on IMF International Financial Statistics (IFS).

```python
from pydeflate import wb_exchange

# Example: Multi-country sales data
data = {
    'country': ['JPN', 'DEU', 'CAN', 'AUS'],
    'year': [2018, 2018, 2019, 2019],
    'sales_lcu': [500000, 800000, 120000, 150000]  # Local currency
}
df = pd.DataFrame(data)

result = wb_exchange(
    data=df,
    source_currency="LCU",      # Each country's currency
    target_currency="USA",      # USD
    id_column="country",
    value_column="sales_lcu",
    target_value_column="sales_usd"
)

print(result[['country', 'year', 'sales_lcu', 'sales_usd']])
```

### Features

- Market exchange rates (yearly average)
- Broad country coverage
- Updated regularly from IFS

**When to use:**

- Standard currency conversions
- Working with World Bank data
- Broad country coverage needed

## PPP Exchange Rates

Purchasing Power Parity (PPP) exchange rates adjust for price level differences between countries.

```python
from pydeflate import wb_exchange_ppp

# Example: Compare living standards across countries
data = {
    'country': ['USA', 'CHN', 'IND', 'BRA'],
    'year': [2019, 2019, 2019, 2019],
    'avg_income_lcu': [65000, 95000, 175000, 38000]  # Local currency
}
df = pd.DataFrame(data)

# Convert using PPP rates for better comparison
result_ppp = wb_exchange_ppp(
    data=df,
    source_currency="LCU",
    target_currency="USA",
    id_column="country",
    value_column="avg_income_lcu",
    target_value_column="avg_income_usd_ppp"
)

# Compare with market rates
result_market = wb_exchange(
    data=df,
    source_currency="LCU",
    target_currency="USA",
    id_column="country",
    value_column="avg_income_lcu",
    target_value_column="avg_income_usd_market"
)

# Merge for comparison
comparison = result_ppp.merge(
    result_market[['country', 'avg_income_usd_market']],
    on='country'
)
print(comparison[['country', 'avg_income_usd_ppp', 'avg_income_usd_market']])
```

### Market vs PPP Rates

| Aspect | Market Rates | PPP Rates |
|--------|-------------|-----------|
| **Purpose** | Financial transactions | Living standard comparisons |
| **Adjusts for** | Supply/demand | Price level differences |
| **Use when** | Trading, investments | Cross-country welfare comparisons |
| **Example** | Currency exchange at bank | Comparing GDP per capita |

**When to use PPP:**

- Comparing living standards
- GDP per capita analysis
- Cross-country welfare studies
- Removing price level bias

**When to use market rates:**

- Financial flows (FDI, trade)
- Actual currency transactions
- Budget conversions

## OECD DAC Exchange Rates

DAC exchange rates are specifically used for Official Development Assistance reporting.

```python
from pydeflate import oecd_dac_exchange

# Example: Convert ODA disbursements to USD
data = {
    'donor': ['GBR', 'FRA', 'DEU', 'JPN'],
    'year': [2015, 2016, 2017, 2018],
    'oda_lcu': [12000, 10000, 24000, 1600000]  # Local currency, millions
}
df = pd.DataFrame(data)

result = oecd_dac_exchange(
    data=df,
    source_currency="LCU",
    target_currency="USA",
    id_column="donor",
    value_column="oda_lcu",
    target_value_column="oda_usd"
)

print(result[['donor', 'year', 'oda_lcu', 'oda_usd']])
```

### Features

- DAC-specific exchange rates
- Consistent with DAC reporting standards
- Aligned with CRS database

**When to use:**

- ODA analysis
- DAC reporting requirements
- Development finance tracking
- Consistency with OECD.Stat

## Converting Between Non-USD Currencies

All sources derive cross-rates from LCU→USD rates. You can convert between any two currencies:

```python
from pydeflate import imf_exchange

# Example: Convert EUR to JPY
data = {
    'country': ['FRA', 'FRA', 'FRA'],
    'year': [2016, 2017, 2018],
    'budget_eur': [1000, 1100, 1200]
}
df = pd.DataFrame(data)

result = imf_exchange(
    data=df,
    source_currency="FRA",      # EUR (France uses EUR)
    target_currency="JPN",      # JPY
    id_column="country",
    value_column="budget_eur",
    target_value_column="budget_jpy"
)

print(result[['year', 'budget_eur', 'budget_jpy']])
```

The conversion uses the formula:
```
EUR → JPY = EUR → USD → JPY
```

## Working with Local Currencies

The special code `"LCU"` (Local Currency Units) allows each country to use its own currency:

```python
from pydeflate import wb_exchange

# Example: Multi-country dataset with mixed currencies
data = {
    'country': ['USA', 'GBR', 'JPN', 'FRA', 'CAN'],
    'year': [2017, 2017, 2017, 2017, 2017],
    'value_lcu': [100, 100, 100, 100, 100]  # Each in local currency
}
df = pd.DataFrame(data)

# Convert all to EUR
result = wb_exchange(
    data=df,
    source_currency="LCU",      # USD, GBP, JPY, EUR, CAD respectively
    target_currency="FRA",      # All to EUR
    id_column="country",
    value_column="value_lcu",
    target_value_column="value_eur"
)

print(result[['country', 'value_lcu', 'value_eur']])
```

## Common Currency Codes

pydeflate accepts both ISO3 country codes and currency abbreviations:

```python
# These are equivalent:
source_currency="USA"  ↔  source_currency="USD"
target_currency="GBR"  ↔  target_currency="GBP"
target_currency="FRA"  ↔  target_currency="EUR"  # For Eurozone
target_currency="JPN"  ↔  target_currency="JPY"
target_currency="CAN"  ↔  target_currency="CAD"
```

For other countries, use the ISO3 country code:

```python
source_currency="CHE"  # Swiss Franc (CHF)
target_currency="AUS"  # Australian Dollar (AUD)
```

## Handling Missing Data

If exchange rate data is missing for a country-year combination, pydeflate:

1. Returns `NaN` for that row
2. Logs a warning with details

```python
from pydeflate import imf_exchange
import pandas as pd

data = {
    'country': ['XYZ'],  # Non-existent country
    'year': [2015],
    'value': [100]
}
df = pd.DataFrame(data)

result = imf_exchange(
    data=df,
    source_currency="XYZ",
    target_currency="USA",
    id_column="country",
    value_column="value",
    target_value_column="value_usd"
)

# result['value_usd'] will be NaN
print(result)
# Warning logged: "Missing exchange rate data for XYZ in 2015"
```

Check for missing data:

```python
# Count missing conversions
missing_count = result['value_usd'].isna().sum()
print(f"Missing conversions: {missing_count}")

# Filter to valid conversions only
valid_data = result.dropna(subset=['value_usd'])
```

## Choosing an Exchange Source

| Use Case | Recommended Function |
|----------|---------------------|
| General currency conversion | `imf_exchange` or `wb_exchange` |
| Living standard comparisons | `wb_exchange_ppp` |
| ODA/development finance | `oecd_dac_exchange` |
| Need future estimates | `imf_exchange` |
| Consistency with World Bank data | `wb_exchange` |
| Consistency with DAC reporting | `oecd_dac_exchange` |

## Complete Example: Multi-Source Analysis

Compare exchange rates across sources:

```python
from pydeflate import imf_exchange, wb_exchange, oecd_dac_exchange, set_pydeflate_path
import pandas as pd

set_pydeflate_path("./data")

# Test data: GBP to USD conversion
data = {
    'country': ['GBR', 'GBR', 'GBR'],
    'year': [2015, 2016, 2017],
    'amount_gbp': [1000, 1000, 1000]
}
df = pd.DataFrame(data)

# Apply all three sources
imf_result = imf_exchange(
    data=df, source_currency="GBR", target_currency="USA",
    id_column="country", value_column="amount_gbp",
    target_value_column="usd_imf"
)

wb_result = wb_exchange(
    data=df, source_currency="GBR", target_currency="USA",
    id_column="country", value_column="amount_gbp",
    target_value_column="usd_wb"
)

dac_result = oecd_dac_exchange(
    data=df, source_currency="GBR", target_currency="USA",
    id_column="country", value_column="amount_gbp",
    target_value_column="usd_dac"
)

# Merge results
comparison = df.copy()
comparison['usd_imf'] = imf_result['usd_imf']
comparison['usd_wb'] = wb_result['usd_wb']
comparison['usd_dac'] = dac_result['usd_dac']

print(comparison)

# Analyze differences
comparison['imf_wb_diff'] = comparison['usd_imf'] - comparison['usd_wb']
comparison['imf_dac_diff'] = comparison['usd_imf'] - comparison['usd_dac']
print(comparison[['year', 'imf_wb_diff', 'imf_dac_diff']])
```

## Getting Exchange Rates Directly

**New in v2.3.0**: You can retrieve exchange rate data as DataFrames without providing your own data. This is useful for:

- Inspecting exchange rates between currencies
- Analyzing exchange rate trends
- Pre-computing rates for manual calculations
- Comparing rates across sources

### Basic Usage

```python
from pydeflate import get_imf_exchange_rates, set_pydeflate_path

set_pydeflate_path("./data")

# Get exchange rates for specific currency pairs
rates = get_imf_exchange_rates(
    source_currency="USD",
    target_currency="EUR",
    countries=["USA", "FRA", "GBR"],  # Optional filter
    years=range(2010, 2024),  # Optional filter
)

# Returns DataFrame with: iso_code, year, exchange_rate
print(rates)
```

### Available Functions

All exchange functions have corresponding "get" versions:

- `get_imf_exchange_rates()` - IMF exchange rates
- `get_wb_exchange_rates()` - World Bank exchange rates
- `get_wb_ppp_rates()` - World Bank PPP conversion rates
- `get_oecd_dac_exchange_rates()` - OECD DAC exchange rates

### Example: Analyzing Exchange Rate Trends

```python
import matplotlib.pyplot as plt
from pydeflate import get_imf_exchange_rates

# Get EUR/USD rates over time
rates = get_imf_exchange_rates(
    source_currency="EUR",
    target_currency="USD",
    years=range(2000, 2024)
)

# Filter for a specific country (e.g., France for EUR)
fra_rates = rates[rates["iso_code"] == "FRA"]

# Plot the trend
plt.figure(figsize=(10, 6))
plt.plot(fra_rates["year"], fra_rates["exchange_rate"], marker='o')
plt.title("EUR/USD Exchange Rate (IMF)")
plt.xlabel("Year")
plt.ylabel("Exchange Rate")
plt.grid(True)
plt.show()
```

### Example: Comparing Sources

```python
from pydeflate import (
    get_imf_exchange_rates,
    get_wb_exchange_rates,
    get_oecd_dac_exchange_rates
)

# Get GBP to USD rates from different sources
imf_rates = get_imf_exchange_rates(
    source_currency="GBR",
    target_currency="USA",
    countries=["GBR"],
    years=[2020, 2021, 2022]
)

wb_rates = get_wb_exchange_rates(
    source_currency="GBR",
    target_currency="USA",
    countries=["GBR"],
    years=[2020, 2021, 2022]
)

dac_rates = get_oecd_dac_exchange_rates(
    source_currency="GBR",
    target_currency="USA",
    countries=["GBR"],
    years=[2020, 2021, 2022]
)

# Compare
import pandas as pd
comparison = pd.DataFrame({
    'year': imf_rates['year'],
    'imf_rate': imf_rates['exchange_rate'],
    'wb_rate': wb_rates['exchange_rate'],
    'dac_rate': dac_rates['exchange_rate']
})

print(comparison)
```

### Example: Manual Currency Conversion

```python
from pydeflate import get_imf_exchange_rates

# Get rates
rates = get_imf_exchange_rates(
    source_currency="GBP",
    target_currency="USD"
)

# Manual conversion
my_value_gbp_2021 = 100  # GBP in 2021
rate_2021 = rates[
    (rates["iso_code"] == "GBR") &
    (rates["year"] == 2021)
]["exchange_rate"].iloc[0]

value_usd = my_value_gbp_2021 * rate_2021
print(f"£{my_value_gbp_2021} in 2021 = ${value_usd:.2f}")
```

## Next Steps

- [**Deflation Guide**](deflate.md) - Combine exchange with deflation
- [**Data Sources**](data-sources.md) - Detailed source comparison
- [**Advanced Topics**](advanced/context.md) - Parallel processing and caching
