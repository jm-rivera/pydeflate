#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pydeflate.get_data.imf_data import _update_weo
from pydeflate.get_data.oecd_data import (
    _update_dac1,
    _update_dac_deflators,
    _update_dac_exchange,
)
from pydeflate.get_data.wb_data import update_indicators

data = {
    "WEO data": _update_weo,
    "DAC1 data": _update_dac1,
    "DAC Deflators": _update_dac_deflators,
    "DAC exchange": _update_dac_exchange,
    "WB data": update_indicators,
}


def update_all_data(data: dict = data) -> None:
    """Run to update all underlying data. It accepts a dictionary of type
    '{source': update_func}. Users should not need to specify it"""

    for source, func in data.items():
        try:
            func()
            print(f"****Successfully updated {source}****\n")
        except:
            print(f"Could not download {source}")


if __name__ == "__main__":
    pass
