__author__ = """Jorge Rivera"""
__version__ = "1.2.10"

from pydeflate.deflate.deflate import deflate
from pydeflate.tools.exchange import exchange
from pydeflate.tools.update_data import update_all_data, warn_updates


def set_pydeflate_path(path):
    from pathlib import Path
    from pydeflate.pydeflate_config import PYDEFLATE_PATHS

    """Set the path to the data folder."""
    global PYDEFLATE_PATHS

    PYDEFLATE_PATHS.data = Path(path).resolve()


# check that data is fresh enough
warn_updates()
