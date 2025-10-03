import pandas as pd
import pytest

from pydeflate import wb_cpi_deflate, wb_gdp_deflate, wb_gdp_linked_deflate
from pydeflate.core.api import BaseDeflate
from pydeflate.core.source import WorldBank


def _base_deflate(*, price_kind: str, to_current: bool, source_currency: str = "USA", target_currency: str = "USA", use_source_codes: bool = False):
    return BaseDeflate(
        base_year=2022,
        deflator_source=WorldBank(),
        exchange_source=WorldBank(),
        price_kind=price_kind,
        source_currency=source_currency,
        target_currency=target_currency,
        use_source_codes=use_source_codes,
        to_current=to_current,
    )


def test_wb_gdp_deflate_with_iso_codes(sample_source_frames):
    data = pd.DataFrame(
        {
            "iso_code": ["USA", "USA", "FRA"],
            "year": [2021, 2022, 2023],
            "value": [200.0, 220.0, 150.0],
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

    result = wb_gdp_deflate(data=data.copy(), base_year=2022)

    assert result["value"].tolist() == pytest.approx(expected["value"].tolist(), rel=1e-6)


def test_wb_gdp_deflate_accepts_source_codes(sample_source_frames):
    data = pd.DataFrame(
        {
            "entity_code": ["001", "124"],
            "year": [2021, 2023],
            "value": [500.0, 640.0],
        }
    )

    base = _base_deflate(
        price_kind="NGDP_D",
        to_current=False,
        use_source_codes=True,
    )
    expected = base.deflate(
        data=data.copy(),
        entity_column="entity_code",
        year_column="year",
        value_column="value",
        year_format=None,
    )

    result = wb_gdp_deflate(
        data=data.copy(),
        base_year=2022,
        id_column="entity_code",
        use_source_codes=True,
    )

    assert result["value"].tolist() == pytest.approx(expected["value"].tolist(), rel=1e-6)


def test_wb_cpi_deflate_to_current_prices(sample_source_frames):
    data = pd.DataFrame(
        {
            "iso_code": ["CAN", "CAN"],
            "year": [2021, 2023],
            "value": [90.0, 120.0],
        }
    )

    base = _base_deflate(price_kind="CPI", to_current=True)
    expected = base.deflate(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        year_format=None,
    )

    result = wb_cpi_deflate(
        data=data.copy(),
        base_year=2022,
        value_column="value",
        to_current=True,
    )

    assert result["value"].tolist() == pytest.approx(expected["value"].tolist(), rel=1e-6)


def test_wb_gdp_linked_deflate_uses_linked_series(sample_source_frames):
    data = pd.DataFrame(
        {
            "iso_code": ["GBR", "GBR"],
            "year": [2021, 2023],
            "value": [100.0, 140.0],
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

    result = wb_gdp_linked_deflate(data=data.copy(), base_year=2022)

    assert result["value"].tolist() == pytest.approx(expected["value"].tolist(), rel=1e-6)
