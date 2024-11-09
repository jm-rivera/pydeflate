__author__ = """Jorge Rivera"""
__version__ = "1.3.10"

from pydeflate.pydeflate_config import setup_logger


def set_pydeflate_path(path):
    from pathlib import Path
    from pydeflate.pydeflate_config import PYDEFLATE_PATHS

    """Set the path to the data folder."""
    global PYDEFLATE_PATHS

    PYDEFLATE_PATHS.data = Path(path).resolve()


logger = setup_logger("pydeflate")


__all__ = [
    "set_pydeflate_path",
    "logger",
]
