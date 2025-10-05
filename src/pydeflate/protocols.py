"""Protocol definitions for type safety and extensibility.

This module defines the core protocols (interfaces) that pydeflate components
must implement. Using protocols enables:
- Type checking without inheritance
- Duck typing with static verification
- Clear contracts for extensibility
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pandas as pd

from pydeflate.sources.common import AvailableDeflators


@runtime_checkable
class SourceProtocol(Protocol):
    """Protocol for data sources (IMF, World Bank, DAC, etc.).

    All data sources must implement these methods to be compatible
    with pydeflate's core deflation and exchange logic.
    """

    name: str
    """Human-readable name of the data source (e.g., 'IMF', 'World Bank')"""

    data: pd.DataFrame
    """The raw data loaded from this source"""

    _idx: list[str]
    """Standard index columns: ['pydeflate_year', 'pydeflate_entity_code', 'pydeflate_iso3']"""

    def lcu_usd_exchange(self) -> pd.DataFrame:
        """Return local currency to USD exchange rates.

        Returns:
            DataFrame with columns: pydeflate_year, pydeflate_entity_code,
            pydeflate_iso3, pydeflate_EXCHANGE
        """
        ...

    def price_deflator(self, kind: AvailableDeflators = "NGDP_D") -> pd.DataFrame:
        """Return price deflator data for the specified type.

        Args:
            kind: Type of deflator (e.g., 'NGDP_D', 'CPI', 'PCPI')

        Returns:
            DataFrame with columns: pydeflate_year, pydeflate_entity_code,
            pydeflate_iso3, pydeflate_{kind}

        Raises:
            ValueError: If the requested deflator kind is not available
        """
        ...

    def validate(self) -> None:
        """Validate that the source data is properly formatted.

        Raises:
            ValueError: If data is empty or improperly formatted
            SchemaValidationError: If data doesn't match expected schema
        """
        ...


@runtime_checkable
class DeflatorProtocol(Protocol):
    """Protocol for deflator objects (price or exchange deflators)."""

    source: SourceProtocol
    """The data source providing deflator data"""

    deflator_type: str
    """Type of deflator: 'price' or 'exchange'"""

    base_year: int
    """The base year for rebasing deflator values (value = 100 at base year)"""

    deflator_data: pd.DataFrame
    """The deflator data, rebased to base_year"""

    def rebase_deflator(self) -> None:
        """Rebase deflator values so that base_year has value 100."""
        ...


@runtime_checkable
class ExchangeProtocol(Protocol):
    """Protocol for exchange rate objects."""

    source: SourceProtocol
    """The data source providing exchange rate data"""

    source_currency: str
    """Source currency code (ISO3 country code or 'LCU')"""

    target_currency: str
    """Target currency code (ISO3 country code)"""

    exchange_data: pd.DataFrame
    """Exchange rate data for converting source_currency to target_currency"""

    def exchange_rate(self, from_currency: str, to_currency: str) -> pd.DataFrame:
        """Calculate exchange rates between two currencies.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            DataFrame with exchange rates and deflators
        """
        ...

    def deflator(self) -> pd.DataFrame:
        """Get exchange rate deflator data.

        Returns:
            DataFrame with columns: pydeflate_year, pydeflate_entity_code,
            pydeflate_iso3, pydeflate_EXCHANGE_D
        """
        ...


@runtime_checkable
class CacheManagerProtocol(Protocol):
    """Protocol for cache management."""

    base_dir: pd.DataFrame
    """Base directory for cached data"""

    def ensure(self, entry, *, refresh: bool = False):
        """Ensure a cache entry exists, downloading if needed.

        Args:
            entry: CacheEntry describing the dataset
            refresh: If True, force re-download

        Returns:
            Path to the cached file
        """
        ...

    def clear(self, key: str | None = None) -> None:
        """Clear cache entries.

        Args:
            key: If provided, clear only this entry. If None, clear all.
        """
        ...


# Type aliases for common DataFrame schemas
ExchangeDataFrame = pd.DataFrame
"""DataFrame containing exchange rate data"""

DeflatorDataFrame = pd.DataFrame
"""DataFrame containing deflator data"""

SourceDataFrame = pd.DataFrame
"""DataFrame containing raw source data"""

UserDataFrame = pd.DataFrame
"""DataFrame provided by users for deflation/exchange"""
