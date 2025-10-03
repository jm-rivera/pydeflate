import pandas as pd
import pytest

from pydeflate import oecd_dac_deflate
from pydeflate.core.api import BaseDeflate
from pydeflate.core.source import DAC


def _base_deflate(
    *,
    to_current: bool,
    source_currency: str,
    target_currency: str,
    use_source_codes: bool = False,
):
    return BaseDeflate(
        base_year=2022,
        deflator_source=DAC(),
        exchange_source=DAC(),
        price_kind="NGDP_D",
        source_currency=source_currency,
        target_currency=target_currency,
        use_source_codes=use_source_codes,
        to_current=to_current,
    )


def test_oecd_dac_deflate_with_source_codes(sample_source_frames):
    data = pd.DataFrame(
        {
            "donor_code": ["001", "826"],
            "year": [2021, 2023],
            "value": [400.0, 220.0],
        }
    )

    base = _base_deflate(
        to_current=False,
        source_currency="USA",
        target_currency="USA",
        use_source_codes=True,
    )
    expected = base.deflate(
        data=data.copy(),
        entity_column="donor_code",
        year_column="year",
        value_column="value",
        year_format=None,
    )

    result = oecd_dac_deflate(
        data=data.copy(),
        base_year=2022,
        id_column="donor_code",
        use_source_codes=True,
    )

    assert result["value"].tolist() == pytest.approx(
        expected["value"].tolist(), rel=1e-6
    )


def test_oecd_dac_deflate_to_current_prices(sample_source_frames):
    data = pd.DataFrame(
        {
            "iso_code": ["CAN", "CAN"],
            "year": [2021, 2023],
            "value": [100.0, 150.0],
        }
    )

    base = _base_deflate(
        to_current=True,
        source_currency="USA",
        target_currency="USA",
    )
    expected = base.deflate(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        year_format=None,
    )

    result = oecd_dac_deflate(
        data=data.copy(),
        base_year=2022,
        value_column="value",
        to_current=True,
    )

    assert result["value"].tolist() == pytest.approx(
        expected["value"].tolist(), rel=1e-6
    )


def test_oecd_dac_deflate_cross_currency(sample_source_frames):
    data = pd.DataFrame(
        {
            "iso_code": ["CAN"],
            "year": [2023],
            "value": [300.0],
        }
    )

    base = _base_deflate(
        to_current=False,
        source_currency="CAN",
        target_currency="USA",
    )
    expected = base.deflate(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        year_format=None,
    )

    result = oecd_dac_deflate(
        data=data.copy(),
        base_year=2022,
        source_currency="CAN",
        target_currency="USA",
    )

    assert result["value"].tolist() == pytest.approx(
        expected["value"].tolist(), rel=1e-6
    )
