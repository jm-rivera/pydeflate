import pandas as pd
import pytest

from pydeflate import wb_exchange_ppp
from pydeflate.core.api import BaseExchange
from pydeflate.core.source import WorldBankPPP


def _base_exchange(source_currency: str):
    return BaseExchange(
        exchange_source=WorldBankPPP(from_lcu=False if source_currency == "USA" else True),
        source_currency=source_currency,
        target_currency="PPP",
    )


def test_wb_exchange_ppp_reverse_regression():
    data = pd.DataFrame(
        {
            "iso_code": ["CAN"],
            "year": [2023],
            "value": [250.0],
        }
    )

    base_forward = _base_exchange("CAN")
    expected_forward = base_forward.exchange(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        target_value_column="value_ppp",
    )

    to_ppp = wb_exchange_ppp(
        data=data.copy(),
        source_currency="CAN",
        value_column="value",
        target_value_column="value_ppp",
    )

    assert to_ppp["value_ppp"].tolist() == pytest.approx(
        expected_forward["value_ppp"].tolist(), rel=1e-6
    )

    base_reverse = _base_exchange("CAN")
    expected_reverse = base_reverse.exchange(
        data=expected_forward.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value_ppp",
        target_value_column="value_lcu",
        reversed_=True,
    )

    back_to_lcu = wb_exchange_ppp(
        data=to_ppp.copy(),
        source_currency="CAN",
        value_column="value_ppp",
        target_value_column="value_lcu",
        reversed_=True,
    )

    assert back_to_lcu["value_lcu"].tolist() == pytest.approx(
        expected_reverse["value_lcu"].tolist(), rel=1e-6
    )
