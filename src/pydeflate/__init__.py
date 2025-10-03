__author__ = """Jorge Rivera"""
__version__ = "2.1.3"

from pydeflate.deflate.deflators import (
    oecd_dac_deflate,
    wb_cpi_deflate,
    wb_gdp_deflate,
    wb_gdp_linked_deflate,
    imf_cpi_deflate,
    imf_gdp_deflate,
    imf_cpi_e_deflate,
)

from pydeflate.deflate.legacy_deflate import deflate
from pydeflate.exchange.exchangers import (
    oecd_dac_exchange,
    wb_exchange,
    wb_exchange_ppp,
    imf_exchange,
)
from pydeflate.pydeflate_config import setup_logger, set_data_dir


def set_pydeflate_path(path):
    """Set the path to the pydeflate data cache directory."""

    return set_data_dir(path)


__all__ = [
    "set_pydeflate_path",
    "oecd_dac_deflate",
    "oecd_dac_exchange",
    "wb_cpi_deflate",
    "wb_gdp_deflate",
    "wb_gdp_linked_deflate",
    "wb_exchange",
    "imf_cpi_deflate",
    "imf_gdp_deflate",
    "imf_cpi_e_deflate",
    "imf_exchange",
    "deflate",
]
