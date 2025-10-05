# Error Handling

pydeflate v2.2,0+ provides a comprehensive exception hierarchy for fine-grained error handling. This guide shows how to handle different error scenarios gracefully.

## Exception Hierarchy

```
PydeflateError (base)
├── DataSourceError
│   └── NetworkError
├── SchemaValidationError
├── CacheError
├── ConfigurationError
├── MissingDataError
└── PluginError
```

All pydeflate exceptions inherit from `PydeflateError`, allowing you to catch all library-specific errors:

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import PydeflateError

try:
    result = imf_gdp_deflate(df, base_year=2015, ...)
except PydeflateError as e:
    print(f"pydeflate error: {e}")
    # Handle any pydeflate-specific error
```

## Exception Types

### NetworkError

Raised when network operations fail (downloads, API calls).

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import NetworkError
import time

def deflate_with_retry(df, max_retries=3):
    """Deflate with automatic retry on network failures."""
    for attempt in range(max_retries):
        try:
            return imf_gdp_deflate(
                data=df,
                base_year=2015,
                source_currency="USA",
                target_currency="USA",
                update=True,  # Force download
                ...
            )
        except NetworkError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Network error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Failed after {max_retries} attempts")
                raise

result = deflate_with_retry(df)
```

**When it occurs:**

- No internet connection
- Source server is down (IMF, World Bank, OECD)
- Request timeout
- DNS resolution failure

**How to handle:**

- Implement retry logic with exponential backoff
- Fall back to cached data (if available)
- Use alternative data source

### ConfigurationError

Raised for invalid parameters or configuration issues.

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import ConfigurationError

try:
    result = imf_gdp_deflate(
        data=df,
        base_year="invalid",  # Should be int
        source_currency="USA",
        target_currency="USA",
        ...
    )
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Fix configuration and fail fast
    raise
```

**Common causes:**

- Invalid base year (not an integer)
- Missing required columns in DataFrame
- Invalid currency codes
- Wrong column types (value column not numeric)

**How to handle:**

- Validate inputs before calling pydeflate
- Log error and fail fast (don't retry)
- Show user-friendly error message

```python
def validate_and_deflate(df, base_year, id_column, value_column):
    """Validate inputs before deflating."""
    # Validate base year
    if not isinstance(base_year, int) or base_year < 1960 or base_year > 2030:
        raise ValueError(f"Invalid base year: {base_year}")

    # Validate DataFrame
    if id_column not in df.columns:
        raise ValueError(f"Column '{id_column}' not found in DataFrame")

    if value_column not in df.columns:
        raise ValueError(f"Column '{value_column}' not found in DataFrame")

    if not df[value_column].dtype.kind in 'iuf':  # int, unsigned, float
        raise ValueError(f"Column '{value_column}' must be numeric")

    try:
        return imf_gdp_deflate(
            data=df,
            base_year=base_year,
            id_column=id_column,
            value_column=value_column,
            ...
        )
    except ConfigurationError as e:
        # Log and re-raise
        print(f"Configuration error (should have been caught): {e}")
        raise
```

### MissingDataError

Raised when required deflator or exchange rate data is unavailable for specific country-year combinations.

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import MissingDataError

try:
    result = imf_gdp_deflate(
        data=df,
        base_year=2015,
        source_currency="USA",
        target_currency="XYZ",  # Non-existent country
        ...
    )
except MissingDataError as e:
    print(f"Missing data: {e}")
    # Try alternative source or fill gaps
```

!!! note
    In most cases, pydeflate doesn't raise `MissingDataError`. Instead, it:

    1. Returns NaN values for missing data
    2. Logs warnings with details

    The exception is raised only for critical missing data scenarios.

**Handling missing data:**

```python
from pydeflate import imf_gdp_deflate, wb_gdp_deflate

# Strategy 1: Filter valid data after conversion
result = imf_gdp_deflate(df, ...)
valid_result = result.dropna(subset=['target_value_column'])

# Strategy 2: Try alternative source
try:
    result = imf_gdp_deflate(df, ...)
except MissingDataError:
    print("IMF data missing, trying World Bank...")
    result = wb_gdp_deflate(df, ...)

# Strategy 3: Fill gaps with custom logic
result = imf_gdp_deflate(df, ...)
result['target_value_column'].fillna(method='ffill', inplace=True)
```

### DataSourceError

Raised when data loading or parsing fails.

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import DataSourceError

try:
    result = imf_gdp_deflate(df, base_year=2015, ...)
except DataSourceError as e:
    print(f"Data source error: {e}")
    # Log error, possibly use cached data
```

**Common causes:**

- Corrupted downloaded file
- Unexpected data format from source
- Parsing errors

**How to handle:**

- Delete cached file and retry with `update=True`
- Report issue to pydeflate maintainers
- Use alternative source

### CacheError

Raised when cache operations fail (read/write permissions, disk full).

```python
from pydeflate import set_pydeflate_path, imf_gdp_deflate
from pydeflate.exceptions import CacheError

try:
    set_pydeflate_path("/read-only/path")  # No write permission
    result = imf_gdp_deflate(df, base_year=2015, update=True, ...)
except CacheError as e:
    print(f"Cache error: {e}")
    # Try alternative cache location
    set_pydeflate_path("/tmp/pydeflate_cache")
    result = imf_gdp_deflate(df, base_year=2015, update=True, ...)
```

**Common causes:**

- No write permission in cache directory
- Disk full
- File locked by another process

**How to handle:**

- Check directory permissions
- Use alternative cache location
- Clear old cache files

### SchemaValidationError

Raised when data fails schema validation (if validation is enabled).

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import SchemaValidationError
from pydeflate.context import pydeflate_session

try:
    with pydeflate_session(enable_validation=True) as ctx:
        result = imf_gdp_deflate(df, base_year=2015, context=ctx, ...)
except SchemaValidationError as e:
    print(f"Validation error: {e}")
    # Disable validation or fix data source
```

See [Schema Validation](validation.md) for more details.

### PluginError

Raised when plugin registration or loading fails.

```python
from pydeflate.plugins import register_source
from pydeflate.exceptions import PluginError

try:
    @register_source("my_source")
    class MySource:
        pass  # Missing required methods
except PluginError as e:
    print(f"Plugin error: {e}")
    # Fix plugin implementation
```

See [Plugin System](plugins.md) for more details.

## Complete Error Handling Example

Robust production code with comprehensive error handling:

```python
from pydeflate import imf_gdp_deflate, wb_gdp_deflate, set_pydeflate_path
from pydeflate.exceptions import (
    NetworkError, ConfigurationError, MissingDataError,
    DataSourceError, CacheError, PydeflateError
)
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def robust_deflate(
    df: pd.DataFrame,
    base_year: int,
    max_retries: int = 3
) -> pd.DataFrame:
    """
    Deflate with comprehensive error handling.

    Strategies:
    - Retry on network errors
    - Validate configuration
    - Fall back to alternative source
    - Handle missing data gracefully
    """

    # Validate inputs
    if not isinstance(base_year, int):
        raise ValueError(f"base_year must be int, got {type(base_year)}")

    if 'iso_code' not in df.columns:
        raise ValueError("DataFrame must have 'iso_code' column")

    if 'value' not in df.columns:
        raise ValueError("DataFrame must have 'value' column")

    # Set cache directory
    try:
        set_pydeflate_path("./pydeflate_data")
    except CacheError:
        logger.warning("Default cache failed, using /tmp")
        set_pydeflate_path("/tmp/pydeflate_cache")

    # Attempt deflation with retry
    for attempt in range(max_retries):
        try:
            result = imf_gdp_deflate(
                data=df,
                base_year=base_year,
                source_currency="USA",
                target_currency="USA",
                id_column="iso_code",
                value_column="value",
                target_value_column="value_constant"
            )

            # Check for missing data
            missing_count = result['value_constant'].isna().sum()
            if missing_count > 0:
                logger.warning(f"{missing_count} rows have missing data")

            return result

        except ConfigurationError as e:
            # Don't retry configuration errors
            logger.error(f"Configuration error: {e}")
            raise

        except NetworkError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Network error: {e}. Retry {attempt+1}/{max_retries} in {wait_time}s")
                time.sleep(wait_time)
            else:
                logger.error(f"Network failed after {max_retries} attempts, trying World Bank")
                try:
                    return wb_gdp_deflate(
                        data=df,
                        base_year=base_year,
                        source_currency="USA",
                        target_currency="USA",
                        id_column="iso_code",
                        value_column="value",
                        target_value_column="value_constant"
                    )
                except PydeflateError as wb_error:
                    logger.error(f"World Bank also failed: {wb_error}")
                    raise

        except (DataSourceError, MissingDataError) as e:
            logger.warning(f"Data source issue: {e}, trying World Bank")
            return wb_gdp_deflate(
                data=df,
                base_year=base_year,
                source_currency="USA",
                target_currency="USA",
                id_column="iso_code",
                value_column="value",
                target_value_column="value_constant"
            )

# Usage
data = {
    'iso_code': ['USA', 'GBR', 'FRA'],
    'year': [2015, 2016, 2017],
    'value': [1000, 1100, 1200]
}
df = pd.DataFrame(data)

try:
    result = robust_deflate(df, base_year=2015)
    print(result)
except Exception as e:
    logger.error(f"Failed to deflate: {e}")
```

## Best Practices

### 1. Catch Specific Exceptions

```python
# Good: Specific exception handling
try:
    result = imf_gdp_deflate(df, ...)
except NetworkError:
    # Retry logic
    pass
except ConfigurationError:
    # Fail fast
    raise
except PydeflateError:
    # Other pydeflate errors
    pass

# Bad: Catching everything
try:
    result = imf_gdp_deflate(df, ...)
except Exception:
    pass  # What went wrong?
```

### 2. Log Errors with Context

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = imf_gdp_deflate(df, base_year=2015, ...)
except PydeflateError as e:
    logger.error(
        f"Deflation failed: {e}",
        extra={
            'base_year': 2015,
            'num_rows': len(df),
            'error_type': type(e).__name__
        }
    )
    raise
```

### 3. Provide Fallbacks

```python
def deflate_with_fallback(df, source='imf'):
    """Try primary source, fall back to secondary."""
    sources = ['imf', 'wb', 'dac']

    for src in sources:
        try:
            if src == 'imf':
                return imf_gdp_deflate(df, ...)
            elif src == 'wb':
                return wb_gdp_deflate(df, ...)
            elif src == 'dac':
                return oecd_dac_deflate(df, ...)
        except PydeflateError as e:
            logger.warning(f"{src} failed: {e}")
            continue

    raise RuntimeError("All sources failed")
```

## Next Steps

- [**Context Management**](context.md) - Advanced configuration and parallel operations
- [**Schema Validation**](validation.md) - Enable data quality checks
- [**Plugin System**](plugins.md) - Create custom data sources with error handling
