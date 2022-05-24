#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pydeflate.get_data.imf_data import IMF
from pydeflate.get_data.oecd_data import OECD, OECD_XE
from pydeflate.get_data.wb_data import WB

DATA = {
    "WEO data": IMF().update,
    "DAC1 data": OECD().update,
    "DAC exchange and deflators": OECD_XE().update,
    "WB data": WB().update,
}


def update_all_data() -> None:
    """Run to update all underlying data. It accepts a dictionary of type
    '{source': update_func}. Users should not need to specify it"""

    for source, func in DATA.items():
        func()
        print(f"****Successfully updated {source}****\n")


if __name__ == "__main__":
    update_all_data()
