# Migration Guide: v1 to v2

pydeflate v2.0 introduces significant API changes for improved clarity and simplicity. This guide helps you migrate from v1.x to v2.x.

## Overview of Changes

### What's New in v2

- **Source-specific functions**: `imf_gdp_deflate()`, `wb_cpi_deflate()`, etc. instead of generic `deflate()`
- **Simplified parameters**: Clearer naming and fewer required parameters
- **Better error handling**: Specific exception types for different failures
- **Source-specific codes**: Support for DAC codes, IMF entity codes, etc.
- **Performance improvements**: Faster data loading and caching

### Breaking Changes

- The generic `deflate()` function is deprecated
- Country code conversion is no longer automatic (use ISO3 codes)
- Some parameter names have changed
- Python 3.11+ required (was 3.10+)

## Quick Migration

### Before (v1.x)

```python
from pydeflate import deflate, set_pydeflate_path

set_pydeflate_path("./data")

result = deflate(
    df=df,
    base_year=2015,
    deflator_source="imf",
    deflator_method="gdp",
    exchange_source="imf",
    source_currency="USA",
    target_currency="FRA",
    id_column="country",
    id_type="ISO3",  # Automatic conversion
    value_col="value",
    target_col="value_constant"
)
```

### After (v2.x)

```python
from pydeflate import imf_gdp_deflate, set_pydeflate_path

set_pydeflate_path("./data")

result = imf_gdp_deflate(
    data=df,  # Renamed from 'df'
    base_year=2015,
    source_currency="USA",
    target_currency="FRA",
    id_column="country",  # Must be ISO3 (no auto-conversion)
    value_column="value",  # Renamed from 'value_col'
    target_value_column="value_constant"  # Renamed from 'target_col'
)
```

## Parameter Mapping

### Core Parameters

| v1.x | v2.x | Notes |
|------|------|-------|
| `df` | `data` | More descriptive name |
| `value_col` | `value_column` | Consistent naming |
| `target_col` | `target_value_column` | Clearer purpose |
| `id_type` | _removed_ | Use ISO3 codes directly |
| `deflator_source` | _function name_ | `imf_gdp_deflate` vs `wb_gdp_deflate` |
| `deflator_method` | _function name_ | `imf_cpi_deflate` vs `imf_gdp_deflate` |
| `exchange_source` | _function name_ | Matched to deflator source |

### Source and Method Selection

**v1.x approach** (single function with parameters):

```python
# IMF GDP
deflate(df, deflator_source="imf", deflator_method="gdp", ...)

# World Bank CPI
deflate(df, deflator_source="wb", deflator_method="cpi", ...)

# OECD DAC
deflate(df, deflator_source="dac", deflator_method="dac", ...)
```

**v2.x approach** (dedicated functions):

```python
# IMF GDP
imf_gdp_deflate(data=df, ...)

# World Bank CPI
wb_cpi_deflate(data=df, ...)

# OECD DAC
oecd_dac_deflate(data=df, ...)
```

## Function Mapping

### Deflation Functions

| v1.x | v2.x |
|------|------|
| `deflate(df, deflator_source="imf", deflator_method="gdp")` | `imf_gdp_deflate(data=df)` |
| `deflate(df, deflator_source="imf", deflator_method="cpi")` | `imf_cpi_deflate(data=df)` |
| `deflate(df, deflator_source="imf", deflator_method="cpi_e")` | `imf_cpi_e_deflate(data=df)` |
| `deflate(df, deflator_source="wb", deflator_method="gdp")` | `wb_gdp_deflate(data=df)` |
| `deflate(df, deflator_source="wb", deflator_method="gdp_linked")` | `wb_gdp_linked_deflate(data=df)` |
| `deflate(df, deflator_source="wb", deflator_method="cpi")` | `wb_cpi_deflate(data=df)` |
| `deflate(df, deflator_source="dac", deflator_method="dac")` | `oecd_dac_deflate(data=df)` |

### Exchange Functions

v2.x adds dedicated exchange functions:

```python
# v2.x only (no v1.x equivalent)
from pydeflate import (
    imf_exchange,
    wb_exchange,
    wb_exchange_ppp,
    oecd_dac_exchange
)
```

## Country Code Handling

### v1.x: Automatic Conversion

v1.x automatically converted country names/codes:

```python
# v1.x - automatic conversion
df['country'] = ['United States', 'United Kingdom', 'France']

result = deflate(
    df=df,
    id_column="country",
    id_type="name",  # Auto-convert from names
    ...
)
```

### v2.x: Explicit ISO3 Codes

v2.x requires ISO3 codes (prevents conversion errors):

```python
# v2.x - use ISO3 codes
df['country'] = ['USA', 'GBR', 'FRA']

result = imf_gdp_deflate(
    data=df,
    id_column="country",  # Must be ISO3
    ...
)
```

**Migration tip**: Convert to ISO3 before calling pydeflate:

```python
# Using country-converter
import country_converter as coco

df['iso3'] = coco.convert(df['country'], to='ISO3')

result = imf_gdp_deflate(data=df, id_column="iso3", ...)
```

Or use `bblocks`:

```python
# Using bblocks
from bblocks import add_iso_codes_column

df = add_iso_codes_column(df, id_column="country")

result = imf_gdp_deflate(data=df, id_column="ISO3", ...)
```

## Complete Migration Examples

### Example 1: GDP Deflation

**v1.x:**

```python
from pydeflate import deflate, set_pydeflate_path

set_pydeflate_path("./data")

result = deflate(
    df=df,
    base_year=2015,
    deflator_source="imf",
    deflator_method="gdp",
    exchange_source="imf",
    source_currency="USA",
    target_currency="USA",
    id_column="country",
    id_type="ISO3",
    value_col="gdp",
    target_col="gdp_2015"
)
```

**v2.x:**

```python
from pydeflate import imf_gdp_deflate, set_pydeflate_path

set_pydeflate_path("./data")

result = imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="USA",
    target_currency="USA",
    id_column="country",
    value_column="gdp",
    target_value_column="gdp_2015"
)
```

### Example 2: CPI with Currency Conversion

**v1.x:**

```python
result = deflate(
    df=df,
    base_year=2020,
    deflator_source="wb",
    deflator_method="cpi",
    exchange_source="wb",
    source_currency="GBR",
    target_currency="USA",
    id_column="country",
    id_type="ISO3",
    value_col="expenditure",
    target_col="expenditure_usd_2020"
)
```

**v2.x:**

```python
from pydeflate import wb_cpi_deflate

result = wb_cpi_deflate(
    data=df,
    base_year=2020,
    source_currency="GBR",
    target_currency="USA",
    id_column="country",
    value_column="expenditure",
    target_value_column="expenditure_usd_2020"
)
```

### Example 3: DAC Deflation

**v1.x:**

```python
# With country names
result = deflate(
    df=df,
    base_year=2018,
    deflator_source="dac",
    deflator_method="dac",
    exchange_source="dac",
    source_currency="USA",
    target_currency="USA",
    id_column="donor",
    id_type="name",
    value_col="oda",
    target_col="oda_2018"
)
```

**v2.x:**

```python
from pydeflate import oecd_dac_deflate

# Option 1: Convert to ISO3 first
df['iso3'] = convert_to_iso3(df['donor'])

result = oecd_dac_deflate(
    data=df,
    base_year=2018,
    source_currency="USA",
    target_currency="USA",
    id_column="iso3",
    value_column="oda",
    target_value_column="oda_2018"
)

# Option 2: Use DAC codes directly
result = oecd_dac_deflate(
    data=df,
    base_year=2018,
    source_currency="USA",
    target_currency="USA",
    id_column="dac_code",
    use_source_codes=True,  # New in v2!
    value_column="oda",
    target_value_column="oda_2018"
)
```

## New Features in v2

### Source-Specific Codes

v2.x supports source-specific country codes:

```python
from pydeflate import oecd_dac_deflate

# Use DAC codes instead of ISO3
result = oecd_dac_deflate(
    data=df,
    base_year=2018,
    id_column="dac_code",
    use_source_codes=True,  # Enable DAC codes
    ...
)
```

### Currency Exchange Only

v2.x adds dedicated exchange functions:

```python
from pydeflate import imf_exchange

# Convert currency without deflation
result = imf_exchange(
    data=df,
    source_currency="GBR",
    target_currency="USA",
    id_column="country",
    value_column="amount_gbp",
    target_value_column="amount_usd"
)
```

### Better Error Handling

v2.x provides specific exceptions:

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import (
    NetworkError,
    ConfigurationError,
    MissingDataError
)

try:
    result = imf_gdp_deflate(df, ...)
except NetworkError:
    # Handle network failures
    pass
except ConfigurationError:
    # Handle invalid parameters
    pass
except MissingDataError:
    # Handle missing data
    pass
```

## Deprecation Timeline

| Version | Status | Notes |
|---------|--------|-------|
| v1.x | Deprecated | Old `deflate()` function still works but warns |
| v2.0-2.1 | Current | `deflate()` function available but deprecated |
| v3.0 | Future | `deflate()` function will be removed |

### Using Deprecated Function

The old `deflate()` function still works in v2.x but shows deprecation warnings:

```python
from pydeflate import deflate  # DeprecationWarning

result = deflate(df, ...)  # Works but warns
```

Suppress warnings (not recommended):

```python
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    result = deflate(df, ...)
```

## Migration Checklist

- [ ] Update to pydeflate v2.x: `pip install pydeflate --upgrade`
- [ ] Replace `deflate()` with source-specific functions
- [ ] Update parameter names: `df` → `data`, `value_col` → `value_column`
- [ ] Convert country identifiers to ISO3 codes
- [ ] Remove `id_type` parameter
- [ ] Test with small dataset to verify results match
- [ ] Update error handling to use specific exception types
- [ ] Review deprecation warnings in logs
- [ ] Update documentation and code comments

## Getting Help

If you encounter issues during migration:

1. Check the [FAQ](faq.md) for common problems
2. Review [examples in the documentation](deflate.md)
3. Open an issue on [GitHub](https://github.com/jm-rivera/pydeflate/issues)

## Next Steps

- [**Getting Started**](getting-started.md) - Learn v2.x basics
- [**Deflation Guide**](deflate.md) - Explore all deflation functions
- [**Advanced Features**](advanced/exceptions.md) - Error handling, contexts, plugins
