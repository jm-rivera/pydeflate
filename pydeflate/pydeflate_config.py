from pathlib import Path
import logging


class PYDEFLATE_PATHS:
    """Class to store the paths to the data and output folders."""

    package = Path(__file__).resolve().parent.parent
    data = package / "pydeflate" / ".pydeflate_data"
    settings = package / "pydeflate" / "settings"
    test_data = package / "tests" / "test_files"


# Create a root logger
logger = logging.getLogger(__name__)

# Create two handlers (terminal and file)
shell_handler = logging.StreamHandler()

# Set levels for the logger, shell and file
logger.setLevel(logging.DEBUG)
shell_handler.setLevel(logging.DEBUG)

# Format the outputs
fmt_shell = "%(levelname)s [%(filename)s: %(funcName)s:] %(message)s"

# Create formatters
shell_formatter = logging.Formatter(fmt_shell)

# Add formatters to handlers
shell_handler.setFormatter(shell_formatter)

# Add handlers to the logger
logger.addHandler(shell_handler)
