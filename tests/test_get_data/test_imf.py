from unittest.mock import patch

import pandas as pd
import pytest

from pydeflate import pydeflate_config, set_pydeflate_path
from pydeflate.get_data.imf_data import IMF

set_pydeflate_path(pydeflate_config.PYDEFLATE_PATHS.test_data)


def ngdp():
    def get_method(*args, **kwargs):
        if "NGDP" in args or "NGDP" in kwargs.values():
            return pd.DataFrame(
                {
                    "iso_code": ["USA", "USA", "USA"],
                    "indicator": ["NGDP", "NGDP", "NGDP"],
                    "year": [2019, 2020, 2021],
                    "value": [100, 150, 200],
                }
            )
        elif "NGDPD" in args or "NGDPD" in kwargs.values():
            return pd.DataFrame(
                {
                    "iso_code": ["USA", "USA", "USA"],
                    "indicator": ["NGDPD", "NGDPD", "NGDPD"],
                    "year": [2019, 2020, 2021],
                    "value": [200, 300, 400],
                }
            )
        else:
            raise ValueError("Unknown indicator")

    return get_method


def test_update_imf():
    def _mock_update_data():
        def update(*args, **kwargs):
            print("mocked update_data")

        return update

    def _mock_update_date():
        def update_update_date(*args, **kwargs):
            print("mocked update_date")

        return update_update_date

    with patch(
        "bblocks.WorldEconomicOutlook.update_data", new_callable=_mock_update_data
    ), patch(
        "pydeflate.get_data.imf_data.update_update_date", new_callable=_mock_update_date
    ) as save:
        IMF().update()


def test_implied_exchange_lcu_usd():
    with patch("pydeflate.get_data.imf_data.IMF.get_method", new_callable=ngdp):
        df = IMF().implied_exchange(direction="lcu_usd")
        assert df.value.mean() == pytest.approx(0.5)


def test_implied_exchange_usd_lcu():
    with patch("pydeflate.get_data.imf_data.IMF.get_method", new_callable=ngdp):
        df = IMF().implied_exchange(direction="usd_lcu")
        assert df.value.mean() == pytest.approx(2)


def test_implied_exchange_fail():
    with patch(
        "pydeflate.get_data.imf_data.IMF.get_method", new_callable=ngdp
    ), pytest.raises(ValueError):
        IMF().implied_exchange(direction="XXX")
