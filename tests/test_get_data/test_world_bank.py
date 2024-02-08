from unittest.mock import patch

import pandas as pd

from pydeflate.get_data.deflators.wb_data import WorldBank, update_world_bank_data
from pydeflate import pydeflate_config, set_pydeflate_path

set_pydeflate_path(pydeflate_config.PYDEFLATE_PATHS.test_data)


class TestWorldBankData(WorldBank):
    def load_data(self, *args, **kwargs):
        print("loaded indicators")

    def update_data(self, *args, **kwargs):
        print("updated data")

    def update(self, *args, **kwargs):
        print("updated")


class TestWorldBank(WorldBank):
    ...


# test update wb data
@patch("pydeflate.get_data.wb_data.update_update_date", return_value=None)
def test_update_world_bank_data(date):
    with patch("pydeflate.get_data.wb_data.WorldBankData", new=TestWorldBankData):
        update_world_bank_data()

    assert date.called


def test_world_bank_available_methods():
    wb = WorldBank()
    assert len(wb._available_methods) > 0


@patch("pydeflate.get_data.wb_data.WorldBank.update", return_value=None)
def test_update_wb_data(update):
    wb = WorldBank()
    wb.update()

    assert update.called


@patch("pydeflate.get_data.wb_data.update_world_bank_data", return_value=pd.DataFrame())
def test_load_wb_data(load):
    wb = WorldBank()

    # Since updating is patched, it will only read the file that's available
    wb.load_data()

    assert len(wb._data) > 0


@patch("pydeflate.get_data.wb_data.update_world_bank_data", return_value=None)
def test_update(update):
    wb = WorldBank()
    wb.update()
    assert update.called
