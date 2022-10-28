import json

import pytest

from pydeflate.config import PYDEFLATE_PATHS
from pydeflate.utils import warn_updates


def test_warn_updates():
    with open(PYDEFLATE_PATHS.data + r"/data_updates.json") as file:
        updates = json.load(file)

    updates["test"] = "2020-01-01"

    with open(PYDEFLATE_PATHS.data + r"/data_updates.json", "w") as outfile:
        json.dump(updates, outfile)

    with pytest.warns(UserWarning):
        warn_updates()

    with open(PYDEFLATE_PATHS.data + r"/data_updates.json") as file:
        updates = json.load(file)

    _ = updates.pop("test")

    with open(PYDEFLATE_PATHS.data + r"/data_updates.json", "w") as outfile:
        json.dump(updates, outfile)
