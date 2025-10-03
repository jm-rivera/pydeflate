import pandas as pd
import pytest
from unittest.mock import MagicMock

from pydeflate.core.deflator import ExchangeDeflator, PriceDeflator


@pytest.fixture
def base_idx():
    return ["pydeflate_year", "pydeflate_entity_code", "pydeflate_iso3"]


def test_price_deflator_rebases_to_base_year(base_idx):
    source = MagicMock()
    source._idx = base_idx
    source.price_deflator.return_value = pd.DataFrame(
        {
            "pydeflate_year": [2021, 2022, 2023],
            "pydeflate_entity_code": ["001"] * 3,
            "pydeflate_iso3": ["USA"] * 3,
            "pydeflate_NGDP_D": [0.9, 1.0, 1.1],
        }
    )

    deflator = PriceDeflator(source=source, kind="NGDP_D", base_year=2022)

    rebased = deflator.deflator_data
    assert list(rebased.loc[:, "pydeflate_NGDP_D"]) == [90.0, 100.0, 110.0]
    source.price_deflator.assert_called_once_with(kind="NGDP_D")


def test_exchange_deflator_raises_when_base_year_missing(base_idx):
    exchange_source = MagicMock()
    exchange_source.deflator.return_value = pd.DataFrame(
        {
            "pydeflate_year": [2021, 2023],
            "pydeflate_entity_code": ["001", "001"],
            "pydeflate_iso3": ["USA", "USA"],
            "pydeflate_EXCHANGE_D": [98.0, 102.0],
        }
    )
    exchange_source.source = MagicMock()
    exchange_source.source._idx = base_idx

    with pytest.raises(ValueError, match="No data found for base year"):
        ExchangeDeflator(source=exchange_source, base_year=2022)


def test_price_deflator_rejects_multiple_value_columns(base_idx):
    source = MagicMock()
    source._idx = base_idx
    source.price_deflator.return_value = pd.DataFrame(
        {
            "pydeflate_year": [2022, 2022],
            "pydeflate_entity_code": ["001", "001"],
            "pydeflate_iso3": ["USA", "USA"],
            "pydeflate_NGDP_D": [100.0, 100.0],
            "pydeflate_CPI": [100.0, 100.0],
        }
    )

    with pytest.raises(ValueError, match="Invalid deflator data format"):
        PriceDeflator(source=source, kind="NGDP_D", base_year=2022)
