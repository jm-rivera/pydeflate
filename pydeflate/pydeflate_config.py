from pathlib import Path
import logging


class PYDEFLATE_PATHS:
    """Class to store the paths to the data and output folders."""

    package = Path(__file__).resolve().parent.parent
    data = package / "pydeflate" / ".pydeflate_data"
    settings = package / "pydeflate" / "settings"
    test_data = package / "tests" / "test_files"


DEFAULT_BASE: int = 2015

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

logger = logging.getLogger("oda_importer")
