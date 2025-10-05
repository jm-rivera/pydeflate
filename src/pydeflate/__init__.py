__author__ = """Jorge Rivera"""
__version__ = "2.1.3"

from pydeflate.deflate.deflators import (
    imf_cpi_deflate,
    imf_cpi_e_deflate,
    imf_gdp_deflate,
    oecd_dac_deflate,
    wb_cpi_deflate,
    wb_gdp_deflate,
    wb_gdp_linked_deflate,
)
from pydeflate.deflate.legacy_deflate import deflate
from pydeflate.exchange.exchangers import (
    imf_exchange,
    oecd_dac_exchange,
    wb_exchange,
    wb_exchange_ppp,
)
from pydeflate.pydeflate_config import set_data_dir, setup_logger

from pydeflate.context import (
    PydeflateContext,
    get_default_context,
    pydeflate_session,
    set_default_context,
    temporary_context,
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
    # Exchange functions
    "imf_exchange",
    "oecd_dac_exchange",
    "wb_exchange",
    "wb_exchange_ppp",
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
]
