import pandas as pd
import pytest

from pydeflate import imf_exchange, wb_exchange
from pydeflate.core.api import BaseExchange
from pydeflate.core.source import IMF, WorldBank


def _base_exchange(source_cls, *, source_currency: str, target_currency: str):
    return BaseExchange(
        exchange_source=source_cls(),
        source_currency=source_currency,
        target_currency=target_currency,
    )


def test_world_bank_exchange_supports_eur_alias():
    data = pd.DataFrame({"iso_code": ["USA"], "year": [2022], "value": [100.0]})

    base = _base_exchange(WorldBank, source_currency="USA", target_currency="EUR")
    expected = base.exchange(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        target_value_column="value_eur",
    )

    result = wb_exchange(
        data=data.copy(),
        source_currency="USA",
        target_currency="EUR",
        value_column="value",
        target_value_column="value_eur",
    )

    assert result["value_eur"].tolist() == pytest.approx(
        expected["value_eur"].tolist(), rel=1e-6
    )


def test_imf_exchange_supports_eur_alias():
    data = pd.DataFrame({"iso_code": ["USA"], "year": [2023], "value": [200.0]})

    base = _base_exchange(IMF, source_currency="USA", target_currency="EUR")
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
        target_currency="EUR",
        value_column="value",
        target_value_column="value_eur",
    )

    assert result["value_eur"].tolist() == pytest.approx(
        expected["value_eur"].tolist(), rel=1e-6
    )
