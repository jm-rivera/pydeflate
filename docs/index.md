# pydeflate

<div class="badges">
  <a href="https://pypi.python.org/pypi/pydeflate"><img src="https://img.shields.io/pypi/v/pydeflate.svg" alt="PyPI version"></a>
  <a href="https://pepy.tech/project/pydeflate"><img src="https://pepy.tech/badge/pydeflate/month" alt="Downloads"></a>
  <a href="https://github.com/jm-rivera/pydeflate"><img src="https://img.shields.io/github/stars/jm-rivera/pydeflate?style=social" alt="GitHub stars"></a>
</div>

**pydeflate** is a Python package for converting between current and constant prices, with built-in currency conversion support. It handles inflation/deflation adjustments using data from multiple authoritative sources (IMF, World Bank, OECD DAC) and combines price deflators with exchange rates for accurate cross-country, cross-currency, and cross-time comparisons.

<div class="quick-links">
  <a href="getting-started/" class="quick-link">Get Started</a>
  <a href="deflation/" class="quick-link">Deflation Guide</a>
  <a href="data-sources/" class="quick-link">Data Sources</a>
  <a href="faq/" class="quick-link">FAQ</a>
</div>

## What can pydeflate do?

- **Convert current prices to constant prices**
- **Convert constant prices to current prices**
- **Convert between currencies** in both current and constant prices
- **Combine deflation and exchange** in a single operation
- **Work with multiple data sources** (IMF, World Bank, OECD DAC)

## Installation

Install pydeflate using pip:

```bash
pip install pydeflate --upgrade
```

## Quick Start

Here's a simple example that converts current USD values to constant 2015 EUR:

```python
from pydeflate import imf_gdp_deflate, set_pydeflate_path
import pandas as pd

# Set up cache directory (only needed once per script)
set_pydeflate_path("path/to/data/folder")

# Your data in current USD prices
data = {
    'iso_code': ['FRA', 'USA', 'GTM'],
    'year': [2017, 2018, 2019],
    'value': [50, 100, 200]
}
df = pd.DataFrame(data)

# Convert to constant 2015 EUR
result = imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="USA",  # USD
    target_currency="FRA",  # EUR
    id_column="iso_code",
    value_column="value",
    target_value_column="value_constant"
)

print(result)
```

## Key Features

### Multiple Data Sources

Choose from three authoritative sources:

- **IMF World Economic Outlook**: GDP deflators, CPI (period average and end-of-period), with future estimates
- **World Bank**: GDP deflators (standard and linked series), CPI, and PPP exchange rates
- **OECD DAC**: Specialized deflators and exchange rates for development assistance

### Flexible Conversions

```python
# Current → Constant prices
imf_gdp_deflate(df, base_year=2015, ...)

# Currency conversion only
imf_exchange(df, source_currency="USA", target_currency="GBR", ...)

# Combined deflation + currency conversion
wb_cpi_deflate(df, base_year=2020, source_currency="LCU", target_currency="USD", ...)
```

### Advanced Features

- **Plugin System**: Register custom data sources
- **Context Management**: Multiple independent cache directories
- **Schema Validation**: Optional data quality checks

## Example Use Cases

### OECD DAC

Track aid flows in constant prices:

```python
# Convert ODA from current USD to constant 2018 USD using DAC deflators
oecd_dac_deflate(
    data=oda_df,
    base_year=2018,
    source_currency="USA",
    target_currency="USA",
    ...
)
```

### World Bank

Compare GDP across countries and time:

```python
# Convert GDP from local currency to constant 2015 USD
wb_gdp_linked_deflate(
    data=gdp_df,
    base_year=2015,
    source_currency="LCU",  # Local currency units
    target_currency="USA",
    ...
)
```

### IMF

Adjust financial data for inflation:

```python
# Convert revenue from current to constant prices using CPI
imf_cpi_deflate(
    data=revenue_df,
    base_year=2020,
    source_currency="GBR",
    target_currency="GBR",  # Same currency, just adjust for inflation
    ...
)
```

## Why pydeflate?

### Why convert to constant prices (and a common currency)?

Most money series mix price changes with quantities. To measure real change, convert nominal values to constant prices (inflation‑adjusted). For cross‑country work, also express everything in a common currency. pydeflate performs both steps—price adjustment and FX conversion—in one, reproducible operation.

### What problem does this solve?
- Illusory growth: Nominal increases can be just inflation. 
- Cross‑country noise: FX swings obscure real trends. 
- Incomparable targets: Budgets/pledges in current prices aren’t comparable across years.

### When should you convert to constant prices?
- Analyses spanning >1–2 years or periods with non‑trivial inflation. 
- Cross‑country / multi‑currency comparisons (aid, revenues, investment). 
- Before computing growth rates, elasticities, or price/volume decompositions.

### Choose the right index
- GDP deflator: economy‑wide prices; good for macro aggregates and public spending.
- CPI: household purchasing power; good for wages, transfers, poverty lines.
- OECD DAC deflators: for official development assistance reporting.
- Sector indices (where available) for narrow baskets.

> Rule of thumb: macro volumes → GDP deflator; household purchasing power → CPI.


### Why use pydeflate?
- **Accurate**: Uses official data from IMF, World Bank, and OECD
- **Simple**: Intuitive API with sensible defaults
- **Flexible**: Multiple sources and deflator types


## Next Steps

- [Getting Started](getting-started.md) - Detailed setup and DataFrame requirements
- [Deflation Guide](deflation.md) - All deflation methods with examples
- [Currency Exchange](exchange.md) - Currency conversion examples
- [Data Sources](data-sources.md) - When to use IMF vs World Bank vs OECD DAC

## Version Note

!!! warning "Breaking Changes in v2.0"
    pydeflate v2 includes API changes that break backwards compatibility. The legacy `deflate()` function is deprecated and will be removed in future versions. Use the new source-specific functions like `imf_gdp_deflate()` instead.

## License

MIT License. See [LICENSE](https://github.com/jm-rivera/pydeflate/blob/main/LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/jm-rivera/pydeflate/issues)
- **Source Code**: [GitHub Repository](https://github.com/jm-rivera/pydeflate)
- **PyPI**: [pydeflate on PyPI](https://pypi.org/project/pydeflate/)
