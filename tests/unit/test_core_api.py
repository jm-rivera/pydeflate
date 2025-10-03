import pandas as pd

from pydeflate.core.api import _base_operation, resolve_common_currencies


class DummyBase:
    def __init__(self, merged):
        self._merged_data = merged
        self._unmatched_data = pd.DataFrame()

    def _merge_pydeflate_data(self, **_):
        # _base_operation expects this hook; our merged data is pre-populated
        return None


def test_resolve_common_currencies_handles_dac_eur_override():
    assert resolve_common_currencies("EUR", "DAC") == "EUI"
    assert resolve_common_currencies("EUR", "World Bank") == "EUR"
    assert resolve_common_currencies("CHF", "DAC") == "CHF"


def test_base_operation_divides_when_deflating():
    merged = pd.DataFrame(
        {
            "value": [100.0, 250.0],
            "pydeflate_deflator": [0.5, 2.0],
            "pydeflate_EXCHANGE": [1.2, 1.2],
        }
    )
    base = DummyBase(merged=merged.copy())

    adjusted = _base_operation(
        base_obj=base,
        data=pd.DataFrame({"value": [100.0, 250.0]}),
        entity_column="iso",
        year_column="year",
        value_column="value",
    )

    assert list(adjusted["value"]) == [200.0, 125.0]


def test_base_operation_multiplies_for_exchange():
    merged = pd.DataFrame(
        {
            "value": [100.0],
            "pydeflate_deflator": [0.5],
            "pydeflate_EXCHANGE": [1.25],
        }
    )
    base = DummyBase(merged=merged.copy())

    adjusted = _base_operation(
        base_obj=base,
        data=pd.DataFrame({"value": [100.0]}),
        entity_column="iso",
        year_column="year",
        value_column="value",
        target_value_column="value_fx",
        exchange=True,
    )

    assert list(adjusted["value_fx"]) == [125.0]


def test_base_operation_respects_reversed_flag():
    merged = pd.DataFrame(
        {
            "value": [120.0],
            "pydeflate_deflator": [0.8],
            "pydeflate_EXCHANGE": [1.1],
        }
    )
    base = DummyBase(merged=merged.copy())

    adjusted = _base_operation(
        base_obj=base,
        data=pd.DataFrame({"value": [120.0]}),
        entity_column="iso",
        year_column="year",
        value_column="value",
        target_value_column="adjusted",
        reversed_=True,
    )

    assert list(adjusted["adjusted"]) == [96.0]
