__author__ = """Jorge Rivera"""
__version__ = "1.3.10"


def set_pydeflate_path(path):
    from pathlib import Path
    from pydeflate.pydeflate_config import PYDEFLATE_PATHS
    from bblocks import set_bblocks_data_path

    """Set the path to the data folder."""
    global PYDEFLATE_PATHS

    PYDEFLATE_PATHS.data = Path(path).resolve()
    set_bblocks_data_path(PYDEFLATE_PATHS.data)


__all__ = [
    "deflate",
    "set_pydeflate_path",
    "get_data",
]
