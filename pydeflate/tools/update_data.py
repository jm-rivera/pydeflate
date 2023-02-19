import datetime
import json

from pydeflate.pydeflate_config import PYDEFLATE_PATHS, logger


def _diff_from_today(date: datetime.datetime):
    """Compare to today"""

    today = datetime.datetime.today()

    return (today - date).days


def warn_updates():

    if not (PYDEFLATE_PATHS.data / "data_updates.json").exists():
        return

    with open(PYDEFLATE_PATHS.data / "data_updates.json") as file:
        updates = json.load(file)

    for source, date in updates.items():
        d = datetime.datetime.strptime(date, "%Y-%m-%d")
        if _diff_from_today(d) > 50:
            message = (
                f'\n\nThe underlying data for "{source}" has not been updated'
                f" in over {_diff_from_today(d)} days. \nIn order to use"
                " pydeflate with the most recent data, please run:\n"
                "`pydeflate.update_all_data()`"
            )
            logger.warning(message)


def update_update_date(source: str):
    """Update the most recent update date for data to today"""

    today = datetime.datetime.today().strftime("%Y-%m-%d")

    # Check to see if specified path contains an update file. Create one if not
    if not (PYDEFLATE_PATHS.data / "data_updates.json").exists():
        updates = {}
        with open(PYDEFLATE_PATHS.data / "data_updates.json", "w") as outfile:
            json.dump(updates, outfile)

    with open(PYDEFLATE_PATHS.data / "data_updates.json") as file:
        updates = json.load(file)

    updates[source] = today

    with open(PYDEFLATE_PATHS.data / "data_updates.json", "w") as outfile:
        json.dump(updates, outfile)


def update_all_data() -> None:
    """Run to update all underlying data."""

    from pydeflate.get_data.imf_data import IMF
    from pydeflate.get_data.oecd_data import OECD
    from pydeflate.get_data.wb_data import WorldBank

    data = {
        "IMF WEO Data": IMF().update,
        "OECD DAC data": OECD().update,
        "WorldBank data": WorldBank().update,
    }

    for source, func in data.items():
        func()
        logger.info(f"****Successfully updated {source}****\n")
