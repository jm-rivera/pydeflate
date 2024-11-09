__author__ = """Jorge Rivera"""
__version__ = "1.3.10"


def set_pydeflate_path(path):
    from pathlib import Path
    from pydeflate.pydeflate_config import PYDEFLATE_PATHS

    """Set the path to the data folder."""
    global PYDEFLATE_PATHS

    PYDEFLATE_PATHS.data = Path(path).resolve()


__all__ = [
    "set_pydeflate_path",
]
