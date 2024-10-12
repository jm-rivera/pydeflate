from datetime import datetime
from pathlib import Path


def check_file_age(file: Path) -> int:
    """Check the age of a WEO file in days.

    Args:
        file (Path): The WEO parquet file to check.

    Returns:
        int: The number of days since the file was created.
    """
    current_date = datetime.today()
    # Extract date from the filename (format: weo_YYYY-MM-DD.parquet)
    file_date = datetime.strptime(file.stem.split("_")[1], "%Y-%m-%d")

    # Return the difference in days between today and the file's date
    return (current_date - file_date).days
