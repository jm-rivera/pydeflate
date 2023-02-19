__author__ = """Jorge Rivera"""
__version__ = "1.3.0"

from pydeflate.deflate.deflate import deflate
from pydeflate.tools.exchange import exchange
from pydeflate.tools.update_data import update_all_data, warn_updates


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
