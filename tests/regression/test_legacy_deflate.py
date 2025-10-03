import pandas as pd
import pytest

from pydeflate.deflate.legacy_deflate import deflate as legacy_deflate
from pydeflate.core.api import BaseDeflate
from pydeflate.core.source import WorldBank


def test_legacy_deflate_emits_warning_and_matches_wrapper():
    data = pd.DataFrame(
        {
            "iso_code": ["USA", "USA"],
            "year": [2021, 2023],
            "value": [210.0, 260.0],
        }
    )

    base = BaseDeflate(
        base_year=2022,
        deflator_source=WorldBank(),
        exchange_source=WorldBank(),
        price_kind="NGDP_D",
        source_currency="USA",
        target_currency="USA",
        to_current=False,
    )
    expected = base.deflate(
        data=data.copy(),
        entity_column="iso_code",
        year_column="year",
        value_column="value",
        year_format=None,
    )

    with pytest.warns(DeprecationWarning):
        result = legacy_deflate(
            df=data.copy(),
            base_year=2022,
            deflator_source="wb",
            deflator_method="gdp",
            exchange_source="wb",
            exchange_method="gdp",
            source_currency="USA",
            target_currency="USA",
            id_column="iso_code",
            date_column="year",
            source_column="value",
            target_column="value",
        )

    assert result["value"].tolist() == pytest.approx(expected["value"].tolist(), rel=1e-6)
