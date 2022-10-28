from pathlib import Path


class PYDEFLATE_PATHS:
    """Class to store the paths to the data and output folders."""

    package = Path(__file__).resolve().parent.parent
    data = package / "pydeflate" / ".pydeflate_data"
