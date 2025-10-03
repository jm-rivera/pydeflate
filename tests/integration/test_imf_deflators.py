import pandas as pd
import pytest

from pydeflate import imf_cpi_deflate, imf_gdp_deflate
from pydeflate.core.api import BaseDeflate
from pydeflate.core.source import IMF


def _base_deflate(*, price_kind: str, to_current: bool, source_currency: str = "USA", target_currency: str = "USA"):
    return BaseDeflate(
        base_year=2022,
        deflator_source=IMF(),
        exchange_source=IMF(),
        price_kind=price_kind,
        source_currency=source_currency,
        target_currency=target_currency,
        to_current=to_current,
    )


def test_imf_gdp_deflate_returns_constant_prices(sample_source_frames):
    data = pd.DataFrame(
        {
            "iso_code": ["USA", "USA", "FRA", "FRA"],
            "year": [2021, 2023, 2021, 2023],
            "value": [150.0, 210.0, 120.0, 144.0],
        }
    )

    base = _base_deflate(price_kind="NGDP_D", to_current=False)
    expected = base.deflate(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        year_format=None,
    )

    result = imf_gdp_deflate(data=data.copy(), base_year=2022, value_column="value")

    assert result["value"].tolist() == pytest.approx(expected["value"].tolist(), rel=1e-6)


def test_imf_cpi_deflate_to_current_prices(sample_source_frames):
    data = pd.DataFrame(
        {
            "iso_code": ["GBR", "GBR"],
            "year": [2021, 2023],
            "value": [80.0, 120.0],
        }
    )

    base = _base_deflate(price_kind="PCPI", to_current=True)
    expected = base.deflate(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        year_format=None,
    )

    result = imf_cpi_deflate(
        data=data.copy(),
        base_year=2022,
        value_column="value",
        to_current=True,
    )

    assert result["value"].tolist() == pytest.approx(expected["value"].tolist(), rel=1e-6)
