__author__ = """Jorge Rivera"""
__email__ = "jorge.rivera@one.org"
__version__ = '1.2.0'


from pydeflate.deflate.deflate import deflate
from pydeflate.tools.exchange import exchange
from pydeflate.tools.update_data import update_all_data
from pydeflate.utils import warn_updates


def set_pydeflate_path(path):
    from pathlib import Path
    from pydeflate.config import PYDEFLATE_PATHS

    """Set the path to the data folder."""
    global PYDEFLATE_PATHS

    PYDEFLATE_PATHS.data = Path(path).resolve()


# check that data is fresh enough
warn_updates()
