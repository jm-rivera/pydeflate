# Plugin System

pydeflate v2.2+ includes a plugin system for registering custom data sources without modifying the package code. This enables integration with proprietary data, alternative public sources, or custom calculations.

## Why Use Plugins?

Built-in sources (IMF, World Bank, OECD DAC) may not cover all use cases:

- Regional central bank data
- Proprietary economic forecasts
- Custom deflator calculations
- Alternative exchange rate sources
- Internal company data

Plugins let you extend pydeflate with custom sources while maintaining the same API.

## Quick Start

Here's a minimal plugin:

```python
from pydeflate.plugins import register_source
import pandas as pd

@register_source("my_central_bank")
class MyCentralBankSource:
    """Custom source from my central bank."""

    def __init__(self, update: bool = False):
        self.name = "my_central_bank"
        self._idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]
        self.data = self._load_data(update)

    def _load_data(self, update: bool) -> pd.DataFrame:
        """Load data from central bank API or file."""
        # Example: Load from CSV
        return pd.read_csv("central_bank_data.csv")

    def lcu_usd_exchange(self) -> pd.DataFrame:
        """Return exchange rate data."""
        return self.data[self._idx + ["pydeflate_EXCHANGE"]]

    def price_deflator(self, kind: str = "NGDP_D") -> pd.DataFrame:
        """Return deflator data."""
        return self.data[self._idx + [f"pydeflate_{kind}"]]

    def validate(self) -> None:
        """Validate data format."""
        required_cols = self._idx + ["pydeflate_EXCHANGE", "pydeflate_NGDP_D"]
        missing = [c for c in required_cols if c not in self.data.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

# Plugin is now registered and ready to use
```

## Plugin Interface

Plugins must implement the `SourceProtocol`:

### Required Methods

#### `__init__(self, update: bool = False)`

Initialize the source and load data.

**Parameters:**
- `update`: If `True`, download fresh data. If `False`, use cached data.

**Required attributes:**
- `self.name`: Source name (string)
- `self._idx`: Index columns (must be `["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]`)
- `self.data`: DataFrame with deflator/exchange data

#### `lcu_usd_exchange() -> pd.DataFrame`

Return exchange rates from local currency to USD.

**Returns:** DataFrame with columns:
- `pydeflate_year`
- `pydeflate_entity_code`
- `pydeflate_iso3`
- `pydeflate_EXCHANGE`: LCU per USD

#### `price_deflator(kind: str) -> pd.DataFrame`

Return price deflator data.

**Parameters:**
- `kind`: Deflator type (e.g., `"NGDP_D"` for GDP deflator, `"PCPI"` for CPI)

**Returns:** DataFrame with columns:
- `pydeflate_year`
- `pydeflate_entity_code`
- `pydeflate_iso3`
- `pydeflate_{kind}`: Deflator index

#### `validate() -> None`

Validate data format and completeness.

**Raises:** Exception if validation fails

## Complete Example

A production-ready plugin with caching, error handling, and multiple deflators:

```python
from pydeflate.plugins import register_source
from pydeflate.exceptions import DataSourceError, NetworkError
import pandas as pd
import requests
from pathlib import Path
import json

@register_source("eurostat")
class EurostatSource:
    """
    Custom source using Eurostat data.

    Provides GDP deflators and exchange rates for EU countries.
    """

    def __init__(self, update: bool = False):
        self.name = "eurostat"
        self._idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]

        # Cache directory
        self.cache_dir = Path.home() / ".pydeflate" / "eurostat"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load or download data
        self.data = self._load_or_fetch(update)

        # Validate
        self.validate()

    def _load_or_fetch(self, update: bool) -> pd.DataFrame:
        """Load from cache or fetch from Eurostat API."""
        cache_file = self.cache_dir / "eurostat_data.parquet"

        # Try cache first
        if not update and cache_file.exists():
            try:
                return pd.read_parquet(cache_file)
            except Exception as e:
                raise DataSourceError(f"Failed to load cached data: {e}")

        # Fetch from API
        try:
            data = self._fetch_from_api()
            # Save to cache
            data.to_parquet(cache_file)
            return data
        except Exception as e:
            raise NetworkError(f"Failed to fetch Eurostat data: {e}")

    def _fetch_from_api(self) -> pd.DataFrame:
        """Fetch data from Eurostat API."""
        # Example API call (simplified)
        url = "https://ec.europa.eu/eurostat/api/dissemination/..."

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse response (simplified)
        raw_data = response.json()

        # Transform to pydeflate format
        return self._transform_data(raw_data)

    def _transform_data(self, raw_data: dict) -> pd.DataFrame:
        """Transform Eurostat data to pydeflate format."""
        # Example transformation
        records = []

        for country in raw_data['countries']:
            iso3 = country['iso3']
            entity_code = country['code']

            for year_data in country['time_series']:
                year = int(year_data['year'])
                gdp_deflator = year_data.get('gdp_deflator', None)
                exchange_rate = year_data.get('exchange_rate', None)

                records.append({
                    'pydeflate_year': year,
                    'pydeflate_entity_code': entity_code,
                    'pydeflate_iso3': iso3,
                    'pydeflate_NGDP_D': gdp_deflator,
                    'pydeflate_EXCHANGE': exchange_rate
                })

        return pd.DataFrame(records)

    def lcu_usd_exchange(self) -> pd.DataFrame:
        """Return EUR/USD and other EU exchange rates."""
        return self.data[self._idx + ["pydeflate_EXCHANGE"]]

    def price_deflator(self, kind: str = "NGDP_D") -> pd.DataFrame:
        """Return price deflator (GDP deflator by default)."""
        col_name = f"pydeflate_{kind}"

        if col_name not in self.data.columns:
            raise ValueError(f"Deflator type '{kind}' not available in Eurostat source")

        return self.data[self._idx + [col_name]]

    def validate(self) -> None:
        """Validate data format."""
        # Check required columns
        required = self._idx + ["pydeflate_EXCHANGE", "pydeflate_NGDP_D"]
        missing = [c for c in required if c not in self.data.columns]

        if missing:
            raise DataSourceError(f"Missing required columns: {missing}")

        # Check for data
        if len(self.data) == 0:
            raise DataSourceError("No data loaded")

        # Check data types
        if not pd.api.types.is_numeric_dtype(self.data["pydeflate_EXCHANGE"]):
            raise DataSourceError("Exchange rate column must be numeric")

        # Check for nulls in critical columns
        null_counts = self.data[self._idx].isnull().sum()
        if null_counts.any():
            raise DataSourceError(f"Null values in index columns: {null_counts[null_counts > 0]}")

# Usage
from pydeflate import BaseDeflate

# The plugin is automatically registered
# Now you can use it like built-in sources
source = EurostatSource(update=True)
print(f"Loaded {len(source.data)} records from Eurostat")
```

## Using Custom Sources

### List Available Sources

```python
from pydeflate.plugins import list_sources

sources = list_sources()
print(sources)
# ['DAC', 'IMF', 'World Bank', 'my_central_bank', 'eurostat']
```

### Check if Source is Registered

```python
from pydeflate.plugins import is_source_registered

if is_source_registered("eurostat"):
    print("Eurostat plugin available")
```

### Get Source Instance

```python
from pydeflate.plugins import get_source

# Get instance of custom source
eurostat = get_source("eurostat", update=False)

# Access data
exchange_data = eurostat.lcu_usd_exchange()
deflator_data = eurostat.price_deflator("NGDP_D")
```

### Use with BaseDeflate

Integrate custom source with pydeflate's deflation engine:

```python
from pydeflate.core.api import BaseDeflate
from pydeflate.plugins import get_source
import pandas as pd

# Get custom source
eurostat = get_source("eurostat")

# Create deflator using custom source
deflator = BaseDeflate(source=eurostat)

# Your data
data = {
    'country': ['FRA', 'DEU', 'ITA'],
    'year': [2015, 2016, 2017],
    'value': [1000, 1100, 1200]
}
df = pd.DataFrame(data)

# Deflate using custom source
result = deflator.deflate(
    data=df,
    base_year=2015,
    source_currency="FRA",
    target_currency="USA",
    id_column="country",
    value_column="value",
    target_value_column="value_constant"
)

print(result)
```

## Data Format Requirements

Your plugin's data must follow pydeflate's schema:

### Index Columns (Required)

```python
self._idx = [
    "pydeflate_year",         # int: Year
    "pydeflate_entity_code",  # str: Source-specific country code
    "pydeflate_iso3"          # str: ISO3 country code
]
```

### Exchange Rate Column (Required)

```python
"pydeflate_EXCHANGE"  # float: Local currency per USD
```

### Deflator Columns (At Least One Required)

```python
"pydeflate_NGDP_D"   # float: GDP deflator (index)
"pydeflate_PCPI"     # float: CPI (index)
"pydeflate_PCPIE"    # float: CPI end-of-period (index)
# ... add custom deflator types
```

### Example Data Structure

```python
data = pd.DataFrame({
    'pydeflate_year': [2015, 2016, 2017],
    'pydeflate_entity_code': ['USA', 'USA', 'USA'],
    'pydeflate_iso3': ['USA', 'USA', 'USA'],
    'pydeflate_EXCHANGE': [1.0, 1.0, 1.0],  # USD to USD
    'pydeflate_NGDP_D': [100.0, 102.0, 104.0],
    'pydeflate_PCPI': [100.0, 101.5, 103.2]
})
```

## Error Handling in Plugins

Use pydeflate's exception hierarchy:

```python
from pydeflate.plugins import register_source
from pydeflate.exceptions import (
    DataSourceError,
    NetworkError,
    SchemaValidationError
)

@register_source("my_source")
class MySource:
    def __init__(self, update: bool = False):
        try:
            self.data = self._load_data(update)
        except requests.RequestException as e:
            raise NetworkError(f"Failed to download data: {e}")
        except ValueError as e:
            raise DataSourceError(f"Data parsing error: {e}")

        self.validate()

    def validate(self):
        """Validate data."""
        if self.data.empty:
            raise DataSourceError("No data loaded")

        required_cols = ["pydeflate_year", "pydeflate_iso3", "pydeflate_EXCHANGE"]
        missing = [c for c in required_cols if c not in self.data.columns]

        if missing:
            raise SchemaValidationError(f"Missing required columns: {missing}")
```

## Testing Plugins

Write tests for your custom source:

```python
import pytest
from pydeflate.plugins import get_source, is_source_registered

def test_plugin_registered():
    """Test plugin is registered."""
    assert is_source_registered("my_central_bank")

def test_plugin_loads_data():
    """Test plugin loads data correctly."""
    source = get_source("my_central_bank", update=False)

    # Check attributes
    assert source.name == "my_central_bank"
    assert hasattr(source, 'data')
    assert len(source.data) > 0

def test_exchange_rates():
    """Test exchange rate data format."""
    source = get_source("my_central_bank")
    exchange_data = source.lcu_usd_exchange()

    # Check columns
    assert "pydeflate_year" in exchange_data.columns
    assert "pydeflate_iso3" in exchange_data.columns
    assert "pydeflate_EXCHANGE" in exchange_data.columns

    # Check data types
    assert exchange_data["pydeflate_EXCHANGE"].dtype == float

def test_deflator():
    """Test deflator data format."""
    source = get_source("my_central_bank")
    deflator_data = source.price_deflator("NGDP_D")

    # Check columns
    assert "pydeflate_NGDP_D" in deflator_data.columns

    # Check values are positive
    assert (deflator_data["pydeflate_NGDP_D"] > 0).all()

def test_validation():
    """Test validation catches errors."""
    source = get_source("my_central_bank")

    # Should not raise
    source.validate()
```

## Best Practices

### 1. Use Caching

Download data once, cache for reuse:

```python
def _load_or_fetch(self, update: bool):
    cache_file = self.cache_dir / "data.parquet"

    if not update and cache_file.exists():
        return pd.read_parquet(cache_file)

    data = self._fetch_from_api()
    data.to_parquet(cache_file)
    return data
```

### 2. Handle Missing Data

```python
def price_deflator(self, kind: str = "NGDP_D"):
    col_name = f"pydeflate_{kind}"

    if col_name not in self.data.columns:
        raise ValueError(f"Deflator '{kind}' not available")

    return self.data[self._idx + [col_name]]
```

### 3. Validate Thoroughly

```python
def validate(self):
    # Check structure
    if self.data.empty:
        raise DataSourceError("No data")

    # Check columns
    required = self._idx + ["pydeflate_EXCHANGE"]
    missing = [c for c in required if c not in self.data.columns]
    if missing:
        raise SchemaValidationError(f"Missing: {missing}")

    # Check data quality
    if (self.data["pydeflate_EXCHANGE"] <= 0).any():
        raise DataSourceError("Exchange rates must be positive")
```

### 4. Document Your Plugin

```python
@register_source("ecb")
class ECBSource:
    """
    European Central Bank data source.

    Provides:
    - EUR/USD and other major currency exchange rates
    - HICP (Harmonized Index of Consumer Prices) for EU countries

    Data coverage:
    - Countries: EU27 + UK, Switzerland, Norway
    - Time range: 1999-present
    - Update frequency: Daily (exchange rates), Monthly (HICP)

    Usage:
        >>> from pydeflate.plugins import get_source
        >>> ecb = get_source("ecb", update=True)
        >>> rates = ecb.lcu_usd_exchange()
    """
```

## Next Steps

- [**Error Handling**](exceptions.md) - Handle plugin errors gracefully
- [**Context Management**](context.md) - Use plugins with custom contexts
- [**Schema Validation**](validation.md) - Validate plugin data
