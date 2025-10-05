"""Pandera schemas for data validation.

This module defines validation schemas for all DataFrame structures used
in pydeflate. This ensures data integrity from external sources and
catches API changes early.
"""

from __future__ import annotations

import pandas as pd

try:
    # New import (pandera >= 0.20)
    import pandera.pandas as pa
    from pandera.pandas import Check, Column, DataFrameSchema
except ImportError:
    # Fallback to old import for older pandera versions
    import pandera as pa
    from pandera import Check, Column, DataFrameSchema

# Column definitions for reuse
YEAR_COLUMN = Column(
    int,
    checks=[
        Check.ge(1960),  # No data before 1960
        Check.le(2100),  # No projections beyond 2100
    ],
    nullable=False,
    description="Year as integer",
)

ENTITY_CODE_COLUMN = Column(
    str,
    checks=[Check(lambda s: s.str.len() <= 10)],
    nullable=False,
    description="Entity code from source (varies by source)",
)

ISO3_COLUMN = Column(
    str,
    checks=[
        Check(lambda s: (s.str.len() == 3) | s.isna()),
    ],
    nullable=True,
    description="ISO3 country code",
)

EXCHANGE_RATE_COLUMN = Column(
    float,
    checks=[
        Check.gt(0),  # Exchange rates must be positive
    ],
    nullable=True,
    description="Exchange rate (LCU per USD)",
)

DEFLATOR_COLUMN = Column(
    float,
    checks=[
        Check.gt(0),  # Deflators must be positive
    ],
    nullable=True,
    description="Price deflator index",
)


class SourceDataSchema(pa.DataFrameModel):
    """Base schema for all data sources.

    All sources must have these minimum columns after processing.
    """

    pydeflate_year: int = pa.Field(ge=1960, le=2100)
    pydeflate_entity_code: str = pa.Field(str_length={"max_value": 10})
    pydeflate_iso3: str | None = pa.Field(nullable=True)

    class Config:
        """Schema configuration."""

        strict = False  # Allow additional columns
        coerce = True  # Attempt type coercion


class ExchangeDataSchema(SourceDataSchema):
    """Schema for exchange rate data."""

    pydeflate_EXCHANGE = EXCHANGE_RATE_COLUMN
    pydeflate_EXCHANGE_D = Column(
        float,
        checks=[Check.gt(0)],
        nullable=True,
        description="Exchange rate deflator (rebased)",
    )

    class Config:
        """Schema configuration."""

        strict = False
        coerce = True


class IMFDataSchema(SourceDataSchema):
    """Schema for IMF WEO data.

    IMF provides GDP deflators, CPI, and exchange rates.
    """

    pydeflate_NGDP_D = Column(
        float,
        checks=[Check.gt(0)],
        nullable=True,
        description="GDP deflator",
    )
    pydeflate_PCPI = Column(
        float,
        checks=[Check.gt(0)],
        nullable=True,
        description="CPI (period average)",
    )
    pydeflate_PCPIE = Column(
        float,
        checks=[Check.gt(0)],
        nullable=True,
        description="CPI (end of period)",
    )
    pydeflate_EXCHANGE = EXCHANGE_RATE_COLUMN

    class Config:
        """Schema configuration."""

        strict = False
        coerce = True


class WorldBankDataSchema(SourceDataSchema):
    """Schema for World Bank data."""

    pydeflate_NGDP_D = Column(
        float,
        checks=[Check.gt(0)],
        nullable=True,
        description="GDP deflator",
    )
    pydeflate_NGDP_DL = Column(
        float,
        checks=[Check.gt(0)],
        nullable=True,
        description="GDP deflator (linked)",
    )
    pydeflate_CPI = Column(
        float,
        checks=[Check.gt(0)],
        nullable=True,
        description="Consumer Price Index",
    )
    pydeflate_EXCHANGE = EXCHANGE_RATE_COLUMN

    class Config:
        """Schema configuration."""

        strict = False
        coerce = True


class DACDataSchema(SourceDataSchema):
    """Schema for OECD DAC data."""

    pydeflate_DAC_DEFLATOR = Column(
        float,
        checks=[Check.gt(0)],
        nullable=True,
        description="DAC deflator",
    )
    pydeflate_NGDP_D = Column(
        float,
        checks=[Check.gt(0)],
        nullable=True,
        description="GDP deflator (computed)",
    )
    pydeflate_EXCHANGE = EXCHANGE_RATE_COLUMN

    class Config:
        """Schema configuration."""

        strict = False
        coerce = True


class UserInputSchema:
    """Validation for user-provided DataFrames.

    This is not a Pandera schema but provides methods to validate
    user input with custom column names.
    """

    @staticmethod
    def validate(
        df,
        id_column: str,
        year_column: str,
        value_column: str,
    ) -> None:
        """Validate user DataFrame has required columns and types.

        Args:
            df: User's DataFrame
            id_column: Name of column with entity identifiers
            year_column: Name of column with year data
            value_column: Name of column with numeric values

        Raises:
            ConfigurationError: If required columns are missing
            SchemaValidationError: If column types are invalid
        """
        from pydeflate.exceptions import ConfigurationError, SchemaValidationError

        # Check required columns exist
        missing_cols = []
        for col_name, col in [
            ("id_column", id_column),
            ("year_column", year_column),
            ("value_column", value_column),
        ]:
            if col not in df.columns:
                missing_cols.append(f"{col_name}='{col}'")

        if missing_cols:
            raise ConfigurationError(
                f"Required columns missing from DataFrame: {', '.join(missing_cols)}"
            )

        # Validate value column is numeric
        if not pd.api.types.is_numeric_dtype(df[value_column]):
            raise SchemaValidationError(
                f"Column '{value_column}' must be numeric, got {df[value_column].dtype}"
            )

        # Validate year column can be converted to datetime
        try:
            pd.to_datetime(df[year_column], errors="coerce")
        except Exception as e:
            raise SchemaValidationError(
                f"Column '{year_column}' cannot be interpreted as dates: {e}"
            )


# Registry of schemas by source name
SCHEMA_REGISTRY: dict[str, type[DataFrameSchema]] = {
    "IMF": IMFDataSchema,
    "World Bank": WorldBankDataSchema,
    "DAC": DACDataSchema,
}


def get_schema_for_source(source_name: str) -> type[DataFrameSchema] | None:
    """Get the appropriate schema for a data source.

    Args:
        source_name: Name of the source (e.g., 'IMF', 'World Bank')

    Returns:
        Schema class for the source, or None if not found
    """
    return SCHEMA_REGISTRY.get(source_name)


def validate_source_data(df, source_name: str) -> None:
    """Validate that source data matches expected schema.

    Args:
        df: DataFrame to validate
        source_name: Name of the source

    Raises:
        SchemaValidationError: If data doesn't match schema
    """
    from pydeflate.exceptions import SchemaValidationError

    schema_class = get_schema_for_source(source_name)
    if schema_class is None:
        # No schema defined for this source, skip validation
        return

    try:
        # Instantiate the schema and validate
        schema = schema_class()
        schema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as e:
        # Collect all validation errors
        error_messages = []
        for error in e.failure_cases.itertuples():
            error_messages.append(f"  - {error.check}: {error.failure_case}")

        raise SchemaValidationError(
            f"Data validation failed for {source_name}:\n" + "\n".join(error_messages),
            source=source_name,
        ) from e
