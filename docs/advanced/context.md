# Context Management

pydeflate v2.2+ introduces a context management system that eliminates global state and enables advanced use cases like parallel processing, custom cache directories, and dependency injection.

## Why Use Contexts?

The traditional approach uses global configuration:

```python
from pydeflate import set_pydeflate_path, imf_gdp_deflate

# Global state - affects all subsequent operations
set_pydeflate_path("./data")

result = imf_gdp_deflate(df, base_year=2015, ...)
```

**Limitations:**

- Can't use different cache directories in the same script
- Difficult to manage logging verbosity per operation

**Context management solves these issues:**

```python
from pydeflate.context import pydeflate_session

# Isolated configuration
with pydeflate_session(data_dir="./cache1") as ctx:
    result1 = imf_gdp_deflate(df, base_year=2015, context=ctx, ...)

with pydeflate_session(data_dir="./cache2") as ctx:
    result2 = wb_gdp_deflate(df, base_year=2020, context=ctx, ...)
```

## Basic Usage

### Session Context

Use `pydeflate_session()` for scoped configuration:

```python
from pydeflate.context import pydeflate_session
from pydeflate import imf_gdp_deflate
import pandas as pd

data = {
    'country': ['USA', 'GBR'],
    'year': [2015, 2016],
    'value': [1000, 1100]
}
df = pd.DataFrame(data)

# Use custom cache directory
with pydeflate_session(data_dir="./my_cache") as ctx:
    result = imf_gdp_deflate(
        data=df,
        base_year=2015,
        source_currency="USA",
        target_currency="USA",
        id_column="country",
        value_column="value",
        target_value_column="value_constant",
        context=ctx  # Pass context
    )

print(result)
# Data cached in ./my_cache
```

### Temporary Context

For testing or one-off operations:

```python
from pydeflate.context import temporary_context
from pydeflate import wb_cpi_deflate

# Creates temporary directory, auto-cleaned on exit
with temporary_context() as ctx:
    result = wb_cpi_deflate(
        data=df,
        base_year=2020,
        context=ctx,
        ...
    )
    # Process result

# Temporary directory automatically deleted
```

## Configuration Options

### Data Directory

Specify where deflator/exchange data is cached:

```python
with pydeflate_session(data_dir="/app/data/pydeflate") as ctx:
    result = imf_gdp_deflate(df, context=ctx, ...)
```

### Logging Level

Control verbosity:

```python
import logging

with pydeflate_session(log_level=logging.DEBUG) as ctx:
    # Detailed debug logs
    result = imf_gdp_deflate(df, context=ctx, ...)

with pydeflate_session(log_level=logging.WARNING) as ctx:
    # Only warnings and errors
    result = wb_gdp_deflate(df, context=ctx, ...)
```

### Schema Validation

Enable data quality checks:

```python
with pydeflate_session(enable_validation=True) as ctx:
    # Schema validation enabled
    result = imf_gdp_deflate(df, context=ctx, ...)
```

See [Schema Validation](validation.md) for details.

### Combined Configuration

```python
import logging

with pydeflate_session(
    data_dir="./cache",
    log_level=logging.INFO,
    enable_validation=True
) as ctx:
    result = imf_gdp_deflate(df, context=ctx, ...)
```

## Default Context

Set a default context for your entire application:

```python
from pydeflate.context import PydeflateContext, set_default_context
from pydeflate import imf_gdp_deflate
import logging

# Create and configure context
ctx = PydeflateContext.create(
    data_dir="/app/cache",
    log_level=logging.INFO,
    enable_validation=False
)

# Set as default
set_default_context(ctx)

# All subsequent operations use this context automatically
result1 = imf_gdp_deflate(df1, base_year=2015, ...)
result2 = wb_gdp_deflate(df2, base_year=2020, ...)
result3 = oecd_dac_deflate(df3, base_year=2018, ...)
```

### Retrieving Default Context

```python
from pydeflate.context import get_default_context

ctx = get_default_context()
print(f"Cache directory: {ctx.data_dir}")
print(f"Logging level: {ctx.log_level}")
```

## Parallel Processing

Contexts are thread-safe, enabling parallel operations:

```python
from pydeflate.context import pydeflate_session
from pydeflate import imf_gdp_deflate, wb_gdp_deflate
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

# Multiple datasets to process
datasets = [df1, df2, df3, df4]

def process_dataset(df, index):
    """Process dataset with isolated context."""
    with pydeflate_session(data_dir=f"./cache_{index}") as ctx:
        return imf_gdp_deflate(
            data=df,
            base_year=2015,
            source_currency="USA",
            target_currency="USA",
            context=ctx,
            ...
        )

# Process in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(process_dataset, df, i)
        for i, df in enumerate(datasets)
    ]

    results = [f.result() for f in futures]

print(f"Processed {len(results)} datasets in parallel")
```

### Shared Cache for Parallel Operations

To use a shared cache (with file locking):

```python
from pydeflate.context import pydeflate_session
from concurrent.futures import ThreadPoolExecutor

def process_with_shared_cache(df, base_year):
    """Multiple threads can safely share same cache."""
    with pydeflate_session(data_dir="./shared_cache") as ctx:
        return imf_gdp_deflate(
            data=df,
            base_year=base_year,
            context=ctx,
            ...
        )

with ThreadPoolExecutor(max_workers=4) as executor:
    # All threads share ./shared_cache (file locking prevents conflicts)
    futures = [
        executor.submit(process_with_shared_cache, df, year)
        for df, year in zip(datasets, base_years)
    ]

    results = [f.result() for f in futures]
```

!!! tip "File Locking"
    pydeflate uses `filelock` for thread-safe cache operations. Multiple threads can safely read/write the same cache directory.

## Environment-Specific Configuration

Use contexts to manage different environments:

```python
from pydeflate.context import PydeflateContext, set_default_context
import os
import logging

# Load environment
environment = os.getenv("ENVIRONMENT", "development")

if environment == "production":
    ctx = PydeflateContext.create(
        data_dir="/var/lib/pydeflate",
        log_level=logging.WARNING,
        enable_validation=True  # Strict validation in prod
    )
elif environment == "development":
    ctx = PydeflateContext.create(
        data_dir="./dev_cache",
        log_level=logging.DEBUG,  # Verbose logs in dev
        enable_validation=False
    )
elif environment == "testing":
    ctx = PydeflateContext.create(
        data_dir="/tmp/pydeflate_test",
        log_level=logging.ERROR,
        enable_validation=True
    )

set_default_context(ctx)
```

## Testing with Contexts

Contexts make testing cleaner:

```python
import pytest
from pydeflate.context import temporary_context
from pydeflate import imf_gdp_deflate
import pandas as pd

def test_deflation():
    """Test deflation without global state contamination."""

    # Arrange
    data = {
        'country': ['USA'],
        'year': [2015],
        'value': [1000]
    }
    df = pd.DataFrame(data)

    # Act
    with temporary_context() as ctx:
        result = imf_gdp_deflate(
            data=df,
            base_year=2015,
            source_currency="USA",
            target_currency="USA",
            id_column="country",
            value_column="value",
            target_value_column="value_constant",
            context=ctx
        )

    # Assert
    assert 'value_constant' in result.columns
    assert result['value_constant'].iloc[0] == 1000  # Base year, no change

    # Temporary cache automatically cleaned up
```
## Migration from Global State

### Before (v2.1 and earlier)

```python
from pydeflate import set_pydeflate_path, imf_gdp_deflate

# Global configuration
set_pydeflate_path("./data")

# All operations use global state
result1 = imf_gdp_deflate(df1, ...)
result2 = wb_gdp_deflate(df2, ...)
```

### After (v2.2+)

```python
from pydeflate.context import PydeflateContext, set_default_context
from pydeflate import imf_gdp_deflate, wb_gdp_deflate

# Option 1: Set default context (backward compatible)
ctx = PydeflateContext.create(data_dir="./data")
set_default_context(ctx)

result1 = imf_gdp_deflate(df1, ...)  # Uses default context
result2 = wb_gdp_deflate(df2, ...)   # Uses default context

# Option 2: Explicit context (recommended for new code)
with pydeflate_session(data_dir="./data") as ctx:
    result1 = imf_gdp_deflate(df1, context=ctx, ...)
    result2 = wb_gdp_deflate(df2, context=ctx, ...)
```

!!! note "Backward Compatibility"
    `set_pydeflate_path()` still works and internally creates a default context. Existing code doesn't need to change.

## Complete Example

Production application with context management:

```python
from pydeflate.context import PydeflateContext, set_default_context
from pydeflate import imf_gdp_deflate, wb_cpi_deflate
from pydeflate.exceptions import PydeflateError
import pandas as pd
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set up context based on environment
env = os.getenv("APP_ENV", "development")

if env == "production":
    context = PydeflateContext.create(
        data_dir="/var/lib/myapp/pydeflate",
        log_level=logging.WARNING,
        enable_validation=True
    )
elif env == "testing":
    context = PydeflateContext.create(
        data_dir="/tmp/pydeflate_test",
        log_level=logging.ERROR,
        enable_validation=True
    )
else:  # development
    context = PydeflateContext.create(
        data_dir="./dev_cache",
        log_level=logging.DEBUG,
        enable_validation=False
    )

set_default_context(context)

# Application code
def process_economic_data(gdp_df, cpi_df):
    """Process economic indicators."""
    try:
        # GDP deflation
        gdp_result = imf_gdp_deflate(
            data=gdp_df,
            base_year=2015,
            source_currency="LCU",
            target_currency="USA",
            id_column="country",
            value_column="gdp",
            target_value_column="gdp_usd_2015"
        )

        # CPI deflation
        cpi_result = wb_cpi_deflate(
            data=cpi_df,
            base_year=2015,
            source_currency="LCU",
            target_currency="LCU",
            id_column="country",
            value_column="price",
            target_value_column="price_2015"
        )

        return gdp_result, cpi_result

    except PydeflateError as e:
        logging.error(f"Deflation failed: {e}")
        raise

# Run application
if __name__ == "__main__":
    # Load data
    gdp_df = pd.read_csv("gdp_data.csv")
    cpi_df = pd.read_csv("cpi_data.csv")

    # Process
    gdp_result, cpi_result = process_economic_data(gdp_df, cpi_df)

    # Save results
    gdp_result.to_csv("gdp_constant.csv", index=False)
    cpi_result.to_csv("cpi_constant.csv", index=False)

    print(f"Processed {len(gdp_result)} GDP observations")
    print(f"Processed {len(cpi_result)} CPI observations")
```

## Next Steps

- [**Error Handling**](exceptions.md) - Robust error handling with contexts
- [**Schema Validation**](validation.md) - Enable validation in context
- [**Plugin System**](plugins.md) - Use custom sources with contexts
