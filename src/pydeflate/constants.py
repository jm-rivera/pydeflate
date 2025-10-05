"""Constants used throughout pydeflate.

Centralizing constants eliminates magic strings and makes refactoring safer.
"""

from __future__ import annotations


class PydeflateColumns:
    """Standard column names used in pydeflate DataFrames."""

    # Index columns
    YEAR = "pydeflate_year"
    ENTITY_CODE = "pydeflate_entity_code"
    ISO3 = "pydeflate_iso3"

    # Data columns
    EXCHANGE = "pydeflate_EXCHANGE"
    EXCHANGE_D = "pydeflate_EXCHANGE_D"

    # Deflator columns
    NGDP_D = "pydeflate_NGDP_D"
    NGDP_DL = "pydeflate_NGDP_DL"
    CPI = "pydeflate_CPI"
    PCPI = "pydeflate_PCPI"
    PCPIE = "pydeflate_PCPIE"
    DAC_DEFLATOR = "pydeflate_DAC_DEFLATOR"

    # Standard index
    STANDARD_INDEX = [YEAR, ENTITY_CODE, ISO3]

    @classmethod
    def deflator_column(cls, kind: str) -> str:
        """Get deflator column name for a given kind.

        Args:
            kind: Deflator type (e.g., 'NGDP_D', 'CPI')

        Returns:
            Full column name with pydeflate_ prefix
        """
        if kind.startswith("pydeflate_"):
            return kind
        return f"pydeflate_{kind}"


class CurrencyCodes:
    """Common currency code mappings."""

    # ISO3 to common codes
    USD = "USA"
    EUR = "EUR"  # For most sources
    EUR_DAC = "EUI"  # For DAC source
    GBP = "GBR"
    JPY = "JPN"
    CAD = "CAN"

    # Special codes
    LCU = "LCU"  # Local Currency Unit
    PPP = "PPP"  # Purchasing Power Parity
    DAC = "DAC"  # DAC members

    # Mapping for user convenience
    COMMON_ALIASES = {
        "USD": USA,
        "EUR": EUR,
        "GBP": GBR,
        "JPY": JPN,
        "CAD": CAN,
    }

    @classmethod
    def resolve(cls, code: str, source: str | None = None) -> str:
        """Resolve a currency code to ISO3.

        Args:
            code: Currency code (USD, EUR, etc.) or ISO3
            source: Data source name (affects EUR mapping for DAC)

        Returns:
            ISO3 country code or special code (LCU, PPP)
        """
        # Handle EUR special case for DAC
        if code == "EUR" and source == "DAC":
            return cls.EUR_DAC

        # Try aliases
        return cls.COMMON_ALIASES.get(code, code)


class DataSources:
    """Names of built-in data sources."""

    IMF = "IMF"
    WORLD_BANK = "World Bank"
    WORLD_BANK_PPP = "World Bank PPP"
    DAC = "DAC"

    # Aliases
    WB = "World Bank"
    OECD = "DAC"

    ALL_SOURCES = [IMF, WORLD_BANK, WORLD_BANK_PPP, DAC]


class CacheDefaults:
    """Default values for caching."""

    TTL_DAYS_IMF = 60  # IMF data updates less frequently
    TTL_DAYS_WB = 30  # World Bank monthly updates
    TTL_DAYS_DAC = 30  # DAC data
    DEFAULT_TTL = 30


class ValidationConfig:
    """Validation configuration."""

    MIN_YEAR = 1960  # No data before 1960
    MAX_YEAR = 2100  # No projections beyond 2100
    MIN_EXCHANGE_RATE = 1e-6  # Extremely low but non-zero
    MAX_EXCHANGE_RATE = 1e6  # Extremely high but finite
