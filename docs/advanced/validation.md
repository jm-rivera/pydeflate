# Schema Validation

pydeflate v2.2+ includes optional schema validation using Pandera. When enabled, it validates data from sources (IMF, World Bank, OECD DAC) against predefined schemas to catch data quality issues early.

## Why Use Validation?

Schema validation helps detect:

- **Type errors**: Wrong data types in columns
- **Missing values**: Unexpected NaNs in critical fields
- **Range violations**: Exchange rates ≤ 0, years outside expected range
- **Schema changes**: Source APIs changing their data structure

This is especially useful in production environments where data quality is critical.

## Enabling Validation

### Method 1: Environment Variable

```bash
export PYDEFLATE_ENABLE_VALIDATION=1
```

Then validation is enabled for all operations:

```python
from pydeflate import imf_gdp_deflate

# Validation automatically enabled
result = imf_gdp_deflate(df, base_year=2015, ...)
```

### Method 2: Context Manager

```python
from pydeflate.context import pydeflate_session
from pydeflate import imf_gdp_deflate

with pydeflate_session(enable_validation=True) as ctx:
    # Validation enabled in this context
    result = imf_gdp_deflate(
        data=df,
        base_year=2015,
        context=ctx,
        ...
    )
```

### Method 3: Default Context

```python
from pydeflate.context import PydeflateContext, set_default_context
from pydeflate import imf_gdp_deflate

# Enable validation globally
ctx = PydeflateContext.create(enable_validation=True)
set_default_context(ctx)

# All operations validate
result = imf_gdp_deflate(df, base_year=2015, ...)
```

## What Gets Validated?

### IMF Data

Schema for IMF World Economic Outlook data:

```python
# pydeflate_year: int, 1980-2030
# pydeflate_iso3: str, ISO3 codes
# pydeflate_entity_code: str, IMF entity codes
# pydeflate_EXCHANGE: float, > 0
# pydeflate_NGDP_D: float, > 0 (GDP deflator)
# pydeflate_PCPI: float, > 0 (CPI)
# pydeflate_PCPIE: float, > 0 (CPI end-of-period)
```

**Checks:**

- Year range: 1980-2030
- Exchange rates and deflators are positive
- ISO3 codes are valid 3-letter strings
- No null values in critical columns

### World Bank Data

Schema for World Bank data:

```python
# pydeflate_year: int, 1960-2030
# pydeflate_iso3: str, ISO3 codes
# pydeflate_entity_code: str, WB country codes
# pydeflate_EXCHANGE: float, > 0
# pydeflate_NGDP_D: float, > 0
# pydeflate_GDP_D_LINKED: float, > 0 (linked deflator)
# pydeflate_PCPI: float, > 0
```

**Checks:**

- Year range: 1960-2030
- Positive values for rates and deflators
- Valid country codes
- No unexpected nulls

### OECD DAC Data

Schema for OECD DAC data:

```python
# pydeflate_year: int, 1960-2030
# pydeflate_iso3: str, ISO3 codes
# pydeflate_entity_code: int, DAC codes
# pydeflate_EXCHANGE: float, > 0
# pydeflate_DAC_DEFLATOR: float, > 0
```

**Checks:**

- Year range: 1960-2030
- DAC entity codes are integers
- Positive exchange rates and deflators
- Valid ISO3 codes

## Handling Validation Errors

When validation fails, a `SchemaValidationError` is raised:

```python
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import SchemaValidationError
from pydeflate.context import pydeflate_session

try:
    with pydeflate_session(enable_validation=True) as ctx:
        result = imf_gdp_deflate(
            data=df,
            base_year=2015,
            context=ctx,
            ...
        )
except SchemaValidationError as e:
    print(f"Validation failed: {e}")
    # Option 1: Disable validation and retry
    # Option 2: Report to pydeflate maintainers
    # Option 3: Use alternative source
```

### Example: Graceful Degradation

```python
from pydeflate import imf_gdp_deflate, wb_gdp_deflate
from pydeflate.exceptions import SchemaValidationError
from pydeflate.context import pydeflate_session
import logging

logger = logging.getLogger(__name__)

def deflate_with_validation(df, base_year):
    """Try with validation, fall back without if it fails."""

    # Try with validation
    try:
        with pydeflate_session(enable_validation=True) as ctx:
            return imf_gdp_deflate(
                data=df,
                base_year=base_year,
                context=ctx,
                source_currency="USA",
                target_currency="USA",
                ...
            )

    except SchemaValidationError as e:
        logger.warning(f"IMF validation failed: {e}")
        logger.info("Trying World Bank without validation")

        # Fall back to World Bank, no validation
        with pydeflate_session(enable_validation=False) as ctx:
            return wb_gdp_deflate(
                data=df,
                base_year=base_year,
                context=ctx,
                source_currency="USA",
                target_currency="USA",
                ...
            )

result = deflate_with_validation(df, base_year=2015)
```

## Performance Impact

Schema validation adds overhead:

- **With validation**: ~10-20% slower (varies by data size)
- **Without validation**: Full speed

```python
import time
from pydeflate import imf_gdp_deflate
from pydeflate.context import pydeflate_session

# Without validation
start = time.time()
with pydeflate_session(enable_validation=False) as ctx:
    result = imf_gdp_deflate(df, base_year=2015, context=ctx, ...)
no_validation_time = time.time() - start

# With validation
start = time.time()
with pydeflate_session(enable_validation=True) as ctx:
    result = imf_gdp_deflate(df, base_year=2015, context=ctx, ...)
validation_time = time.time() - start

print(f"Without validation: {no_validation_time:.2f}s")
print(f"With validation: {validation_time:.2f}s")
print(f"Overhead: {(validation_time/no_validation_time - 1) * 100:.1f}%")
```

## When to Enable Validation

### Enable in:

- **Production environments**: Catch data issues before they affect results
- **Automated pipelines**: Fail fast on data problems
- **Initial development**: Understand data structure and constraints
- **After source updates**: Verify new data matches expected schema

### Disable in:

- **Performance-critical applications**: Minimize overhead
- **Trusted environments**: Data quality already verified
- **Development/testing**: Faster iteration
- **Batch processing**: Validate once, then disable

## Custom Validation for Plugins

Add validation to your custom sources:

```python
from pydeflate.plugins import register_source
from pydeflate.exceptions import SchemaValidationError
import pandas as pd
import pandera as pa

@register_source("my_source")
class MySource:
    """Custom source with validation."""

    # Define schema
    SCHEMA = pa.DataFrameSchema({
        "pydeflate_year": pa.Column(int, pa.Check.between(1960, 2030)),
        "pydeflate_iso3": pa.Column(str, pa.Check.str_length(3)),
        "pydeflate_entity_code": pa.Column(str),
        "pydeflate_EXCHANGE": pa.Column(float, pa.Check.greater_than(0)),
        "pydeflate_NGDP_D": pa.Column(float, pa.Check.greater_than(0))
    })

    def __init__(self, update: bool = False):
        self.name = "my_source"
        self._idx = ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]
        self.data = self._load_data(update)

        # Validate
        self.validate()

    def validate(self):
        """Validate data against schema."""
        try:
            self.SCHEMA.validate(self.data)
        except pa.errors.SchemaError as e:
            raise SchemaValidationError(f"Schema validation failed: {e}")

    def lcu_usd_exchange(self):
        return self.data[self._idx + ["pydeflate_EXCHANGE"]]

    def price_deflator(self, kind="NGDP_D"):
        return self.data[self._idx + [f"pydeflate_{kind}"]]
```

## Inspecting Schemas

View the schemas used by pydeflate:

```python
from pydeflate.schemas import IMFDataSchema, WorldBankDataSchema, DACDataSchema

# IMF schema
print("IMF Schema:")
print(IMFDataSchema.to_yaml())

# World Bank schema
print("\nWorld Bank Schema:")
print(WorldBankDataSchema.to_yaml())

# DAC schema
print("\nDAC Schema:")
print(DACDataSchema.to_yaml())
```

## Validation in Testing

Use validation to ensure test data matches production:

```python
import pytest
from pydeflate.context import pydeflate_session
from pydeflate import imf_gdp_deflate
from pydeflate.exceptions import SchemaValidationError

def test_deflation_with_validation():
    """Test deflation with schema validation."""

    # Arrange
    data = {
        'country': ['USA', 'GBR'],
        'year': [2015, 2016],
        'value': [1000, 1100]
    }
    df = pd.DataFrame(data)

    # Act & Assert
    with pydeflate_session(enable_validation=True) as ctx:
        # Should not raise SchemaValidationError
        result = imf_gdp_deflate(
            data=df,
            base_year=2015,
            context=ctx,
            source_currency="USA",
            target_currency="USA",
            id_column="country",
            value_column="value",
            target_value_column="value_constant"
        )

    assert 'value_constant' in result.columns

def test_invalid_data_raises_validation_error():
    """Test that invalid source data raises SchemaValidationError."""

    # This test would need to mock invalid data from source
    # Example structure:
    with pydeflate_session(enable_validation=True) as ctx:
        # If source data is invalid, should raise
        with pytest.raises(SchemaValidationError):
            # ... operation that triggers validation error
            pass
```

## Production Example

Comprehensive production setup with validation:

```python
from pydeflate import imf_gdp_deflate
from pydeflate.context import PydeflateContext, set_default_context
from pydeflate.exceptions import SchemaValidationError, PydeflateError
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure based on environment
env = os.getenv("ENVIRONMENT", "development")

if env == "production":
    # Enable validation in production
    ctx = PydeflateContext.create(
        data_dir="/var/lib/app/pydeflate",
        log_level=logging.WARNING,
        enable_validation=True  # Strict validation
    )
elif env == "development":
    # No validation in dev for speed
    ctx = PydeflateContext.create(
        data_dir="./dev_cache",
        log_level=logging.DEBUG,
        enable_validation=False
    )

set_default_context(ctx)

# Application code
def process_data(df):
    """Process data with validation in production."""
    try:
        result = imf_gdp_deflate(
            data=df,
            base_year=2015,
            source_currency="USA",
            target_currency="USA",
            ...
        )

        logger.info(f"Successfully processed {len(result)} rows")
        return result

    except SchemaValidationError as e:
        # Validation failed - data quality issue
        logger.error(f"Schema validation failed: {e}")
        logger.error("Source data does not match expected schema")
        # Alert monitoring system
        raise

    except PydeflateError as e:
        logger.error(f"Deflation error: {e}")
        raise

# Run
if __name__ == "__main__":
    df = load_data()  # Your data loading
    result = process_data(df)
    save_results(result)
```

## Next Steps

- [**Error Handling**](exceptions.md) - Handle validation errors gracefully
- [**Context Management**](context.md) - Configure validation via contexts
- [**Plugin System**](plugins.md) - Add validation to custom sources
