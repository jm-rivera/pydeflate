__author__ = """Jorge Rivera"""
__version__ = "1.3.9"

from pydeflate.deflate.deflate import deflate
from pydeflate.tools.exchange import exchange
from pydeflate.tools.update_data import update_all_data, warn_updates
from pydeflate.get_data.oecd_data import update_dac1
from pydeflate import get_data


def set_pydeflate_path(path):
    from pathlib import Path
    from pydeflate.pydeflate_config import PYDEFLATE_PATHS
    from bblocks import set_bblocks_data_path

    """Set the path to the data folder."""
    global PYDEFLATE_PATHS

    PYDEFLATE_PATHS.data = Path(path).resolve()
    set_bblocks_data_path(PYDEFLATE_PATHS.data)


# check that data is fresh enough
warn_updates()


__all__ = [
    "deflate",
    "exchange",
    "update_all_data",
    "set_pydeflate_path",
    "get_data",
    "update_dac1",
]
