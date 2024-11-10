import logging
from pathlib import Path


class PYDEFLATE_PATHS:
    """Class to store the paths to the data and output folders."""

    package = Path(__file__).resolve().parent.parent
    data = package / "pydeflate" / ".pydeflate_data"
    settings = package / "pydeflate" / "settings"
    test_data = package / "tests" / "test_files"


def setup_logger(name) -> logging.Logger:
    """Set up the logger.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger.

    """
    logger_ = logging.getLogger(name)
    logger_.setLevel(logging.INFO)

    # Only add handlers if the logger has none to avoid duplication
    if not logger_.hasHandlers():
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s:\n %(message)s"
        )
        console_handler.setFormatter(formatter)

        logger_.addHandler(console_handler)
        logger_.propagate = False

    return logger_


logger = setup_logger("pydeflate")
