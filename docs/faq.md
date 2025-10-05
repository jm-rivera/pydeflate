# FAQ and Troubleshooting

Common questions and solutions for pydeflate users.

## Installation and Setup

### How do I install pydeflate?

```bash
pip install pydeflate --upgrade
```

Requires Python 3.11 or higher.

### Do I need to configure anything before using pydeflate?

Yes, set the cache directory:

```python
from pydeflate import set_pydeflate_path

set_pydeflate_path("./pydeflate_data")
```

This only needs to be done once per script/session.

### Where should I store the cache?

Choose a persistent location:

- **Development**: `./pydeflate_data` (project directory)
- **Production**: `/var/lib/myapp/pydeflate` (system directory)
- **User scripts**: `~/.pydeflate` (home directory)

The cache stores downloaded data from IMF, World Bank, and OECD.

### Can I use environment variables for configuration?

Yes:

```bash
export PYDEFLATE_DATA_DIR="/path/to/cache"
```

Then you don't need to call `set_pydeflate_path()`.

## Data Requirements

### What format should my data be in?

pandas DataFrame with at least:

1. **Country column**: ISO3 codes (e.g., `USA`, `GBR`, `FRA`)
2. **Year column**: Integer, string, or datetime
3. **Value column**: Numeric (int or float)

Example:

```python
data = {
    'country': ['USA', 'GBR', 'FRA'],
    'year': [2015, 2016, 2017],
    'value': [1000, 1100, 1200]
}
df = pd.DataFrame(data)
```

### My data uses country names, not ISO3 codes. What should I do?

Convert to ISO3 codes first:

```python
# Option 1: Using country_converter
import country_converter as coco
df['iso3'] = coco.convert(df['country_name'], to='ISO3')

# Option 2: Using bblocks-places
from bblocks import places
df["iso3_code"] = places.resolve_places(df["country_name"], to_type="iso3_code")

```

Then use the ISO3 column with pydeflate.

### Can I use DAC codes or other country codes?

Yes, with `use_source_codes=True`:

```python
from pydeflate import oecd_dac_deflate

result = oecd_dac_deflate(
    data=df,
    id_column="dac_code",
    use_source_codes=True,  # Enable DAC codes
    ...
)
```

This works when your data uses the same coding system as the source.

## Currency Codes

### What currency codes are supported?

Use ISO3 country codes or common abbreviations:

| Code | Country | Currency |
|------|---------|----------|
| `USA` or `USD` | United States | US Dollar |
| `FRA` or `EUR` | France (Eurozone) | Euro |
| `GBR` or `GBP` | United Kingdom | British Pound |
| `JPN` or `JPY` | Japan | Japanese Yen |
| `CAN` or `CAD` | Canada | Canadian Dollar |

For other currencies, use the ISO3 country code.

### What does `LCU` mean?

LCU stands for "Local Currency Units" — each country's own currency:

```python
# Convert from local currencies to USD
result = imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="LCU",  # GBP for UK, EUR for France, etc.
    target_currency="USA",
    ...
)
```

### Can I convert EUR to JPY directly?

Yes, pydeflate handles cross-rates automatically:

```python
result = imf_exchange(
    data=df,
    source_currency="FRA",  # EUR
    target_currency="JPN",  # JPY
    ...
)
```

The conversion uses: EUR → USD → JPY.

## Data Sources

### Which source should I use?

| Use Case | Recommended Source |
|----------|-------------------|
| GDP analysis | IMF or World Bank |
| Long time series (20+ years) | World Bank (linked deflator) |
| Consumer prices | IMF or World Bank CPI |
| Development assistance (ODA) | OECD DAC |
| Future estimates | IMF |
| PPP comparisons | World Bank |

See [Data Sources](data-sources.md) for detailed comparison.

### Do different sources give different results?

Yes, slightly. Sources use different methodologies and update schedules:

```python
# Compare sources
imf_result = imf_gdp_deflate(df, base_year=2015, ...)
wb_result = wb_gdp_deflate(df, base_year=2015, ...)

# Typically differ by <1% for most countries/years
```

Choose the source that matches your analysis context.

### How often is data updated?

| Source | Update Frequency           |
|--------|----------------------------|
| IMF WEO | Biannual (April, October)  |
| World Bank | Annual (September-October) |
| OECD DAC | Biannual (April, December) |

pydeflate warns if cached data is >50 days old.

## Troubleshooting

### I'm getting NaN values in my results. Why?

Common causes:

1. **Missing deflator/exchange data** for that country-year
2. **Invalid country codes** (not recognized)
3. **Year out of range** (e.g., before 1960)

Check warnings in logs:

```python
import logging
logging.basicConfig(level=logging.WARNING)

# Run deflation - warnings show missing data
result = imf_gdp_deflate(df, ...)
```

Filter to valid data:

```python
valid_result = result.dropna(subset=['target_value_column'])
```

### How do I update cached data?

Set `update=True`:

```python
result = imf_gdp_deflate(
    data=df,
    base_year=2015,
    update=True,  # Download fresh data
    ...
)
```

Or delete cache manually:

```bash
rm -rf ./pydeflate_data/*
```

### I'm getting "No such file or directory" errors

You forgot to set the cache directory:

```python
from pydeflate import set_pydeflate_path

set_pydeflate_path("./pydeflate_data")  # Must call this first

# Now proceed
result = imf_gdp_deflate(df, ...)
```

### Downloads are failing. What should I do?

Network issues:

1. **Check internet connection**
2. **Check firewall/proxy** (IMF, World Bank, OECD access)
3. **Retry with exponential backoff**:

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import NetworkError
import time

def deflate_with_retry(df, max_retries=3):
    for attempt in range(max_retries):
        try:
            return imf_gdp_deflate(df, base_year=2015, update=True, ...)
        except NetworkError:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"Retry in {wait}s...")
                time.sleep(wait)
            else:
                raise

result = deflate_with_retry(df)
```

### My results don't match published figures. Why?

Possible reasons:

1. **Different base year**: Published figures may use different base year
2. **Different source**: IMF vs World Bank vs OECD use different data
3. **Different deflator type**: GDP deflator vs CPI
4. **Data revision**: Sources periodically revise historical data
5. **Rounding differences**: Calculation precision


### Can I use pydeflate offline?

Yes, if you've cached the data:

```python
# First run with internet (downloads data)
set_pydeflate_path("./cache")
result = imf_gdp_deflate(df, base_year=2015, update=True, ...)

# Subsequent runs work offline
result = imf_gdp_deflate(df, base_year=2015, ...)  # Uses cache
```

### Can I process data in parallel?

Yes, use thread-safe contexts:

```python
from pydeflate.context import pydeflate_session
from concurrent.futures import ThreadPoolExecutor

def process_dataset(df):
    with pydeflate_session(data_dir="./cache") as ctx:
        return imf_gdp_deflate(df, context=ctx, ...)

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_dataset, datasets))
```

File locking prevents cache conflicts.

## Advanced Topics

### Can I create custom data sources?

Yes, using the plugin system:

```python
from pydeflate.plugins import register_source

@register_source("my_source")
class MySource:
    def __init__(self, update: bool = False):
        self.name = "my_source"
        self._idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]
        self.data = self._load_data(update)

    def lcu_usd_exchange(self):
        return self.data[self._idx + ["pydeflate_EXCHANGE"]]

    def price_deflator(self, kind="NGDP_D"):
        return self.data[self._idx + [f"pydeflate_{kind}"]]

    def validate(self):
        # Validation logic
        pass
```

See [Plugin System](advanced/plugins.md) for details.

### How do I handle errors robustly?

Use specific exception handling:

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import (
    NetworkError,
    ConfigurationError,
    MissingDataError
)

try:
    result = imf_gdp_deflate(df, base_year=2015, ...)
except NetworkError:
    # Retry or use cached data
    pass
except ConfigurationError:
    # Fix parameters and fail fast
    raise
except MissingDataError:
    # Try alternative source
    result = wb_gdp_deflate(df, base_year=2015, ...)
```

See [Error Handling](advanced/exceptions.md) for comprehensive examples.

### Can I use different cache directories for different projects?

Yes, using contexts:

```python
from pydeflate.context import pydeflate_session

# Project 1
with pydeflate_session(data_dir="./project1_cache") as ctx:
    result1 = imf_gdp_deflate(df1, context=ctx, ...)

# Project 2
with pydeflate_session(data_dir="./project2_cache") as ctx:
    result2 = wb_cpi_deflate(df2, context=ctx, ...)
```

See [Context Management](advanced/context.md).

## Migration from v1

### How do I migrate from pydeflate v1.x?

Replace `deflate()` with source-specific functions:

**v1.x:**
```python
result = deflate(df, deflator_source="imf", deflator_method="gdp", ...)
```

**v2.x:**
```python
result = imf_gdp_deflate(data=df, ...)
```

See [Migration Guide](migration.md) for complete details.

### Will v1 code still work?

Yes, but with deprecation warnings. Update to v2 API for:

- Better performance
- Clearer error messages
- New features (plugins, contexts, validation)

### When will v1 API be removed?

The `deflate()` function will be removed in v3.0 (no timeline yet). Migrate now to avoid breaking changes.

## Getting Help

### Where can I report bugs?

Open an issue on GitHub: [https://github.com/jm-rivera/pydeflate/issues](https://github.com/jm-rivera/pydeflate/issues)

Include:

- pydeflate version (`pip show pydeflate`)
- Python version
- Minimal reproducible example
- Error messages and stack traces

### Where can I ask questions?

1. Check this FAQ
2. Review the [documentation](index.md)
3. Open a GitHub issue for support

### How can I contribute?

Contributions welcome!

- Report bugs and request features on GitHub
- Submit pull requests for fixes and enhancements
- Improve documentation
- Share use cases and examples

See the [GitHub repository](https://github.com/jm-rivera/pydeflate) for contribution guidelines.

## Common Patterns

### Convert multiple DataFrames

```python
datasets = [df1, df2, df3]

results = [
    imf_gdp_deflate(df, base_year=2015, ...)
    for df in datasets
]
```

### Compare sources

```python
imf_result = imf_gdp_deflate(df, base_year=2015, ...)
wb_result = wb_gdp_deflate(df, base_year=2015, ...)

comparison = df.merge(
    imf_result[['country', 'year', 'value_imf']],
    on=['country', 'year']
).merge(
    wb_result[['country', 'year', 'value_wb']],
    on=['country', 'year']
)
```

## Next Steps

- [**Getting Started**](getting-started.md) - Basic setup and usage
- [**Deflation Guide**](deflation.md) - Comprehensive deflation examples
- [**Advanced Topics**](advanced/exceptions.md) - Error handling, contexts, plugins
