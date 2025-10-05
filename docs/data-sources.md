# Data Sources

pydeflate currently supports three authoritative data sources: IMF, World Bank, and OECD DAC. This guide helps you choose the right source for your use case.

## Source Comparison

| Feature | IMF                       | World Bank             | OECD DAC                   |
|---------|---------------------------|------------------------|----------------------------|
| **Primary Use** | Economic forecasting      | Development indicators | Development assistance     |
| **Country Coverage** | ~190 countries            | ~200 countries         | ~60 donors |
| **Time Range** | 1980-present + forecasts  | 1960-present           | 1960-present               |
| **Update Frequency** | Biannual (April, October) | Annual                 | Annual                     |
| **Deflators** | GDP, CPI (avg & EOP)      | GDP, GDP linked, CPI   | DAC deflator               |
| **Exchange Rates** | WEO rates                 | WDI rates              | DAC exchange rates         |
| **Future Estimates** | Yes (~5 years)            | No                     | No                         |
| **PPP Rates** | No                        | Yes                    | No                         |

## IMF World Economic Outlook

### Overview

The International Monetary Fund's World Economic Outlook (WEO) database provides economic indicators with estimates for future years.

**Data URL:** [https://www.imf.org/en/Publications/WEO](https://www.imf.org/en/Publications/WEO)

### Available Functions

```python
from pydeflate import (
    imf_gdp_deflate,    # GDP deflator
    imf_cpi_deflate,    # CPI (period average)
    imf_cpi_e_deflate,  # CPI (end-of-period)
    imf_exchange        # Exchange rates
)
```

### Strengths

- **Future estimates**: Includes ~5 year forecasts for GDP deflators and CPI
- **Comprehensive**: Covers ~190 countries with consistent methodology
- **Frequent updates**: Published twice yearly (April, October)
- **Economic focus**: Ideal for macroeconomic analysis

### Limitations

- Estimates subject to revision
- Exchange rates are derived based on WEO data (instead of published directly as an indicator)

### When to Use IMF

Use IMF data when you need:

- **Future year estimates**
  ```python
  # Project 2024-2026 aid budgets to constant 2023 prices
  imf_gdp_deflate(df, base_year=2023, ...)
  ```

- **Consistency with IMF publications**
  ```python
  # Ensure compatibility with IMF reports
  imf_cpi_deflate(df, base_year=2020, ...)
  ```

- **End-of-period CPI** for financial reporting
  ```python
  # December year-end adjustments
  imf_cpi_e_deflate(df, base_year=2018, ...)
  ```

### Data Characteristics

- **GDP deflator**: Broad measure of price changes in the economy
- **CPI (period average)**: Average monthly CPI across the year
- **CPI (end-of-period)**: December CPI value
- **Exchange rates**: Yearly average, derived from WEO data

## World Bank

### Overview

The World Bank provides a comprehensive collection of development indicators spanning decades.

**Data URL:** [https://databank.worldbank.org/](https://databank.worldbank.org/)

### Available Functions

```python
from pydeflate import (
    wb_gdp_deflate,         # GDP deflator
    wb_gdp_linked_deflate,  # Linked GDP deflator
    wb_cpi_deflate,         # CPI
    wb_exchange,            # Market exchange rates
    wb_exchange_ppp         # PPP exchange rates
)
```

### Strengths

- **Deep history**: Data from 1960 onwards
- **Broad coverage**: ~200 countries and territories
- **Linked deflators**: Includes estimates for some gaps in the series.
- **PPP rates**: Purchasing power parity comparisons
- **Development focus**: Tailored for development indicators

### Limitations

- No future estimates
- Annual updates
- Some historical gaps for smaller countries

### When to Use World Bank

Use World Bank data when you need:

- **Long time series** (20+ years)
  ```python
  # Analyze trends from 1980-2020
  wb_gdp_linked_deflate(df, base_year=2010, ...)
  ```

- **PPP comparisons** for living standards
  ```python
  # Compare GDP per capita across countries
  wb_exchange_ppp(df, source_currency="LCU", target_currency="USA", ...)
  ```

- **Consistency with World Bank data**
  ```python
  # Match World Development Indicators
  wb_gdp_deflate(df, base_year=2015, ...)
  ```

- **GDP series with some gaps filled**
  ```python
  # Handle breaks in deflator series
  wb_gdp_linked_deflate(df, base_year=2015, ...)
  ```

### Data Characteristics

- **GDP deflator**: Annual percentage change, standard series
- **Linked GDP deflator**: Annual percentage change, with some gaps filled
- **CPI**: Consumer price index (period average)
- **Exchange rates (market)**: From IMF IFS, yearly average
- **Exchange rates (PPP)**: Purchasing power parity conversion factors

## OECD Development Assistance Committee

### Overview

The OECD DAC provides specialized deflators and exchange rates for Official Development Assistance (ODA), maintained specifically for aid flow analysis.

**Data URL:** [https://www.oecd.org/dac/](https://www.oecd.org/dac/)

### Available Functions

```python
from pydeflate import (
    oecd_dac_deflate,   # DAC deflator
    oecd_dac_exchange   # DAC exchange rates
)
```

### Strengths

- **ODA-specific**: Designed for development assistance analysis
- **DAC standard**: Official methodology for aid reporting
- **Consistency**: Aligned with OECD.Stat and CRS database
- **Donor focus**: Optimized for donor country reporting

### Limitations

- Limited to ODA context (not suitable for general economic analysis)
- Smaller country coverage (donors)
- Single deflator type (no separate CPI)

### When to Use OECD DAC

Use DAC data when working with:

- **Official Development Assistance**
  ```python
  # Convert ODA to constant prices
  oecd_dac_deflate(df, base_year=2018, ...)
  ```

- **DAC reporting requirements**
  ```python
  # Ensure compliance with DAC standards
  oecd_dac_deflate(df, base_year=2020, ...)
  ```

- **Creditor Reporting System (CRS) data**
  ```python
  # Match CRS deflation methodology
  oecd_dac_exchange(df, source_currency="LCU", target_currency="USA", ...)
  ```

### DAC Codes

DAC uses its own country coding system. Enable with `use_source_codes=True`:

```python
# DAC donor codes (examples):
# 4   = France
# 12  = United Kingdom
# 302 = United States
# 701 = Japan

data = {
    'dac_code': [4, 12, 302, 701],
    'year': [2015, 2016, 2017, 2018],
    'oda': [11400, 18700, 30900, 15500]
}

result = oecd_dac_deflate(
    data=pd.DataFrame(data),
    base_year=2018,
    id_column="dac_code",
    use_source_codes=True,  # Use DAC codes
    ...
)
```

### Data Characteristics

- **DAC deflator**: Composite deflator for aid flows
- **Exchange rates**: Yearly average rates used in DAC reporting

## Choosing the Right Source

### Decision Tree

```
┌─ Need future estimates?
│  └─ YES → Use IMF
│
├─ Working with ODA data?
│  └─ YES → Use OECD DAC
│
├─ Need PPP exchange rates?
│  └─ YES → Use World Bank (wb_exchange_ppp)
│
├─ Time series > 20 years?
│  └─ YES → Use World Bank (wb_gdp_linked_deflate)
│
└─ General economic analysis?
   └─ Use IMF or World Bank
```

### By Use Case

| Use Case | Recommended Source |
|----------|-------------------|
| GDP analysis, current/recent years | IMF (`imf_gdp_deflate`) |
| GDP analysis, historical (1960-2000) | World Bank (`wb_gdp_linked_deflate`) |
| Consumer prices, inflation | IMF (`imf_cpi_deflate`) or World Bank (`wb_cpi_deflate`) |
| Wage/salary adjustments | IMF (`imf_cpi_deflate`) |
| Cross-country welfare comparison | World Bank (`wb_exchange_ppp`) |
| ODA/development finance | OECD DAC (`oecd_dac_deflate`) |
| Budget forecasting (future years) | IMF (`imf_gdp_deflate`) |
| Year-end financial reporting | IMF (`imf_cpi_e_deflate`) |
| Long-term economic trends | World Bank (`wb_gdp_linked_deflate`) |

## Comparing Sources

You can compare results across sources:

```python
from pydeflate import imf_gdp_deflate, wb_gdp_deflate, set_pydeflate_path
import pandas as pd

set_pydeflate_path("./data")

# Test data
data = {
    'country': ['USA', 'GBR', 'FRA'],
    'year': [2015, 2016, 2017],
    'value': [1000, 1000, 1000]
}
df = pd.DataFrame(data)

# Apply both sources
imf_result = imf_gdp_deflate(
    df, base_year=2015, source_currency="USA", target_currency="USA",
    id_column="country", value_column="value", target_value_column="value_imf"
)

wb_result = wb_gdp_deflate(
    df, base_year=2015, source_currency="USA", target_currency="USA",
    id_column="country", value_column="value", target_value_column="value_wb"
)

# Merge and compare
comparison = df.merge(
    imf_result[['country', 'year', 'value_imf']],
    on=['country', 'year']
).merge(
    wb_result[['country', 'year', 'value_wb']],
    on=['country', 'year']
)

comparison['difference'] = comparison['value_imf'] - comparison['value_wb']
print(comparison)
```

## Data Update Schedule

| Source | Release Schedule | Typical Release Months |
|--------|------------------|------------------------|
| IMF WEO | Biannual         | April, October         |
| World Bank | Annual           | September-October      |
| OECD DAC | Biannual         | April, December        |

pydeflate caches data locally and checks for updates. If cached data is >50 days old, you'll see a warning to refresh.

## Data Attribution

pydeflate relies on publicly available data from:

- **IMF World Economic Outlook**: [https://www.imf.org/en/Publications/WEO](https://www.imf.org/en/Publications/WEO)
- **World Bank DataBank**: [https://databank.worldbank.org/](https://databank.worldbank.org/)
- **OECD DAC**: [https://www.oecd.org/dac/](https://www.oecd.org/dac/)

This data is provided based on the terms and conditions set by the original sources.

## Next Steps

- [**Deflation Guide**](deflate.md) - Apply deflators from each source
- [**Currency Exchange**](exchange.md) - Use exchange rates from each source
- [**Advanced Topics**](advanced/plugins.md) - Register custom data sources
