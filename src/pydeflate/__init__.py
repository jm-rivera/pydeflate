__author__ = """Jorge Rivera"""
__version__ = "2.3.0"

from pydeflate.deflate.deflators import (
    imf_cpi_deflate,
    imf_cpi_e_deflate,
    imf_gdp_deflate,
    oecd_dac_deflate,
    wb_cpi_deflate,
    wb_gdp_deflate,
    wb_gdp_linked_deflate,
)
from pydeflate.deflate.get_deflators import (
    get_imf_cpi_deflators,
    get_imf_cpi_e_deflators,
    get_imf_gdp_deflators,
    get_oecd_dac_deflators,
    get_wb_cpi_deflators,
    get_wb_gdp_deflators,
    get_wb_gdp_linked_deflators,
)
from pydeflate.deflate.legacy_deflate import deflate
from pydeflate.exchange.exchangers import (
    imf_exchange,
    oecd_dac_exchange,
    wb_exchange,
    wb_exchange_ppp,
)
from pydeflate.exchange.get_rates import (
    get_imf_exchange_rates,
    get_oecd_dac_exchange_rates,
    get_wb_exchange_rates,
    get_wb_ppp_rates,
)
from pydeflate.pydeflate_config import set_data_dir, setup_logger

from pydeflate.context import (
    PydeflateContext,
    get_default_context,
    pydeflate_session,
    set_default_context,
    temporary_context,
)
from pydeflate.groups import GroupTreatment
from pydeflate.groups.emu import (
    all_members as _all_members,
    members_for_year as _members_for_year,
)
from pydeflate.exceptions import (
    CacheError,
    ConfigurationError,
    DataSourceError,
    MissingDataError,
    NetworkError,
    PluginError,
    PydeflateError,
    SchemaValidationError,
)
from pydeflate.plugins import (
    get_source,
    is_source_registered,
    list_sources,
    register_source,
)


def set_pydeflate_path(path):
    """Set the path to the pydeflate data cache directory."""

    return set_data_dir(path)


def emu_members(year: int | None = None) -> list[str]:
    """Return ISO3 codes of EMU (eurozone) member countries.

    Args:
        year: If specified, return members as of that year.
              If None, return all countries that have ever been members.

    Returns:
        Sorted list of ISO3 country codes.

    Examples:
        >>> emu_members(1999)
        ['AUT', 'BEL', 'DEU', 'ESP', 'FIN', 'FRA', 'IRL', 'ITA', 'LUX', 'NLD', 'PRT']
        >>> len(emu_members(2023))
        20
    """
    if year is None:
        return _all_members()
    return _members_for_year(year)


def set_group_treatment(treatment: str) -> None:
    """Set how pydeflate treats ALL country groups in source data.

    Args:
        treatment: "source" (default), "fixed", or "dynamic"
            - source: Use the data source's own published aggregate
            - fixed: GDP-weighted average using current membership for all years
            - dynamic: GDP-weighted average using actual membership per year

    Example:
        >>> import pydeflate
        >>> pydeflate.set_group_treatment("fixed")
        >>> result = pydeflate.imf_gdp_deflate(df, base_year=2015, source_currency="EUR", ...)
    """
    from pydeflate.groups import GroupTreatment as GT, _registry

    _registry.default_treatment = GT(treatment)


def configure_group(
    group: str,
    *,
    treatment: str,
    members_year: int | None = None,
) -> None:
    """Configure how a specific group's deflators are computed.

    Args:
        group: Group key (e.g., "EMU"). See ``list_groups()`` for available groups.
        treatment: "source", "fixed", or "dynamic"
        members_year: Pin membership to a specific year (optional)

    Example:
        >>> pydeflate.configure_group("EMU", treatment="fixed", members_year=2019)
    """
    from pydeflate.groups import _registry

    _registry.configure(group, treatment=treatment, members_year=members_year)


def reset_group_config() -> None:
    """Reset all group configurations to defaults."""
    from pydeflate.groups import _registry

    _registry.reset()


__all__ = [
    # Deflation functions
    "deflate",
    "imf_cpi_deflate",
    "imf_cpi_e_deflate",
    "imf_gdp_deflate",
    "oecd_dac_deflate",
    "wb_cpi_deflate",
    "wb_gdp_deflate",
    "wb_gdp_linked_deflate",
    # Get deflators functions
    "get_imf_cpi_deflators",
    "get_imf_cpi_e_deflators",
    "get_imf_gdp_deflators",
    "get_oecd_dac_deflators",
    "get_wb_cpi_deflators",
    "get_wb_gdp_deflators",
    "get_wb_gdp_linked_deflators",
    # Exchange functions
    "imf_exchange",
    "oecd_dac_exchange",
    "wb_exchange",
    "wb_exchange_ppp",
    # Get exchange rates functions
    "get_imf_exchange_rates",
    "get_oecd_dac_exchange_rates",
    "get_wb_exchange_rates",
    "get_wb_ppp_rates",
    # Configuration
    "set_pydeflate_path",
    "setup_logger",
    # Context management
    "PydeflateContext",
    "get_default_context",
    "pydeflate_session",
    "set_default_context",
    "temporary_context",
    # Exceptions
    "CacheError",
    "ConfigurationError",
    "DataSourceError",
    "MissingDataError",
    "NetworkError",
    "PluginError",
    "PydeflateError",
    "SchemaValidationError",
    # Plugin system
    "get_source",
    "is_source_registered",
    "list_sources",
    "register_source",
    # Group treatment
    "GroupTreatment",
    "emu_members",
    "set_group_treatment",
    "configure_group",
    "reset_group_config",
]
