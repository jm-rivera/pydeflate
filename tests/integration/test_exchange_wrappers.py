import pandas as pd
import pytest

from pydeflate import (
    imf_exchange,
    oecd_dac_exchange,
    wb_exchange,
    wb_exchange_ppp,
)
from pydeflate.core.api import BaseExchange
from pydeflate.core.source import DAC, IMF, WorldBank, WorldBankPPP


def _base_exchange(source_cls, *, source_currency: str, target_currency: str, use_source_codes: bool = False):
    return BaseExchange(
        exchange_source=source_cls(),
        source_currency=source_currency,
        target_currency=target_currency,
        use_source_codes=use_source_codes,
    )


def test_imf_exchange_converts_usd_to_eur(sample_source_frames):
    data = pd.DataFrame({"iso_code": ["USA"], "year": [2022], "value": [100.0]})

    base = _base_exchange(IMF, source_currency="USA", target_currency="FRA")
    expected = base.exchange(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        target_value_column="value_eur",
    )

    result = imf_exchange(
        data=data.copy(),
        source_currency="USA",
        target_currency="FRA",
        value_column="value",
        target_value_column="value_eur",
    )

    assert result["value_eur"].tolist() == pytest.approx(expected["value_eur"].tolist(), rel=1e-6)


def test_wb_exchange_supports_reversed_flow():
    data = pd.DataFrame(
        {
            "iso_code": ["USA", "USA"],
            "year": [2021, 2023],
            "value": [120.0, 240.0],
        }
    )

    base = _base_exchange(WorldBank, source_currency="USA", target_currency="FRA")
    expected = base.exchange(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        target_value_column="value_eur",
        reversed_=True,
    )

    converted = wb_exchange(
        data=data.copy(),
        source_currency="USA",
        target_currency="FRA",
        value_column="value",
        target_value_column="value_eur",
        reversed_=True,
    )

    assert converted["value_eur"].tolist() == pytest.approx(
        expected["value_eur"].tolist(), rel=1e-6
    )


def test_oecd_dac_exchange_uses_source_codes():
    data = pd.DataFrame(
        {
            "donor_code": ["001"],
            "year": [2022],
            "value": [500.0],
        }
    )

    base = _base_exchange(DAC, source_currency="USA", target_currency="CAN", use_source_codes=True)
    expected = base.exchange(
        data=data.copy(),
        entity_column="donor_code",
        year_column="year",
        value_column="value",
        target_value_column="value_converted",
    )

    converted = oecd_dac_exchange(
        data=data.copy(),
        source_currency="USA",
        target_currency="CAN",
        id_column="donor_code",
        use_source_codes=True,
        value_column="value",
        target_value_column="value_converted",
    )

    assert converted["value_converted"].tolist() == pytest.approx(
        expected["value_converted"].tolist(), rel=1e-6
    )


def test_wb_exchange_ppp_round_trip():
    data = pd.DataFrame(
        {
            "iso_code": ["USA", "USA"],
            "year": [2021, 2022],
            "value": [100.0, 150.0],
        }
    )

    base_forward = _base_exchange(WorldBankPPP, source_currency="USA", target_currency="PPP")
    to_ppp_expected = base_forward.exchange(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        target_value_column="value_ppp",
    )
    to_ppp = wb_exchange_ppp(
        data=data.copy(),
        source_currency="USA",
        value_column="value",
        target_value_column="value_ppp",
    )

    assert to_ppp["value_ppp"].tolist() == pytest.approx(
        to_ppp_expected["value_ppp"].tolist(), rel=1e-6
    )

    base_reverse = _base_exchange(
        WorldBankPPP,
        source_currency="USA",
        target_currency="PPP",
    )
    back_expected = base_reverse.exchange(
        data=to_ppp_expected.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value_ppp",
        target_value_column="value_usd",
        reversed_=True,
    )

    back_to_usd = wb_exchange_ppp(
        data=to_ppp.copy(),
        source_currency="USA",
        value_column="value_ppp",
        target_value_column="value_usd",
        reversed_=True,
    )

    assert back_to_usd["value_usd"].tolist() == pytest.approx(
        back_expected["value_usd"].tolist(), rel=1e-6
    )
