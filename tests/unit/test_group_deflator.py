"""Tests for GDP-weighted group deflator computation."""

import pandas as pd
import pytest

from pydeflate.core.group_deflator import compute_group_deflator
from pydeflate.groups.emu import members_for_year
from pydeflate.sources.common import enforce_pyarrow_types


def _make_source_data() -> pd.DataFrame:
    """Create minimal source data with 2 EMU members (DEU, FRA) and USA."""
    records = []
    for iso3, code, gdp_values, deflator_values, exchange_values in [
        (
            "DEU",
            "134",
            [4000.0, 4200.0, 4400.0],
            [95.0, 100.0, 106.0],
            [0.84, 0.85, 0.86],
        ),
        (
            "FRA",
            "250",
            [2800.0, 3000.0, 3200.0],
            [96.0, 100.0, 108.0],
            [0.84, 0.85, 0.86],
        ),
        (
            "USA",
            "001",
            [23000.0, 25000.0, 27000.0],
            [98.0, 100.0, 103.0],
            [1.0, 1.0, 1.0],
        ),
        (
            "EUR",
            "G163",
            [None, None, None],
            [95.5, 100.0, 107.0],
            [0.84, 0.85, 0.86],
        ),
    ]:
        for i, year in enumerate([2021, 2022, 2023]):
            records.append(
                {
                    "pydeflate_year": year,
                    "pydeflate_entity_code": code,
                    "pydeflate_iso3": iso3,
                    "pydeflate_NGDP_D": deflator_values[i],
                    "pydeflate_EXCHANGE": exchange_values[i],
                    "pydeflate_EXCHANGE_D": [96.0, 100.0, 104.0][i],
                    "pydeflate_NGDPD": gdp_values[i],
                }
            )
    return enforce_pyarrow_types(pd.DataFrame.from_records(records))


class TestComputeGroupDeflator:
    def test_fixed_computes_weighted_average(self):
        data = _make_source_data()
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        eur = result[result["pydeflate_iso3"] == "EUR"]

        # 2022: DEU=4200, FRA=3000, both deflator=100 -> weighted=100
        assert eur[eur["pydeflate_year"] == 2022]["pydeflate_NGDP_D"].iloc[
            0
        ] == pytest.approx(100.0, abs=0.1)

        # 2023: DEU weight=4400/7600=0.5789, FRA weight=3200/7600=0.4211
        # Weighted = 0.5789*106 + 0.4211*108 = 106.84
        val_2023 = eur[eur["pydeflate_year"] == 2023]["pydeflate_NGDP_D"].iloc[0]
        assert val_2023 != 107.0
        assert val_2023 == pytest.approx(106.84, abs=0.1)

    def test_non_group_rows_unchanged(self):
        data = _make_source_data()
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        usa = result[result["pydeflate_iso3"] == "USA"]
        assert usa["pydeflate_NGDP_D"].tolist() == [98.0, 100.0, 103.0]

    def test_exchange_rate_not_modified(self):
        data = _make_source_data()
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        eur = result[result["pydeflate_iso3"] == "EUR"]
        assert eur["pydeflate_EXCHANGE"].tolist() == [0.84, 0.85, 0.86]

    def test_missing_ngdpd_falls_back_to_equal_weight(self):
        data = _make_source_data()
        data.loc[data["pydeflate_iso3"].isin(["DEU", "FRA"]), "pydeflate_NGDPD"] = None
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        eur = result[result["pydeflate_iso3"] == "EUR"]
        # Equal weight: (106 + 108) / 2 = 107.0
        val_2023 = eur[eur["pydeflate_year"] == 2023]["pydeflate_NGDP_D"].iloc[0]
        assert val_2023 == pytest.approx(107.0, abs=0.1)

    def test_pin_year_uses_fixed_membership(self):
        data = _make_source_data()
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=True,
            pin_year=2020,
        )
        eur = result[result["pydeflate_iso3"] == "EUR"]
        assert eur["pydeflate_NGDP_D"].notna().all()

    def test_no_members_in_data_preserves_source(self):
        data = _make_source_data()
        data = data[~data["pydeflate_iso3"].isin(["DEU", "FRA"])]
        result = compute_group_deflator(
            data,
            price_kind="NGDP_D",
            group_iso3="EUR",
            get_members=members_for_year,
            dynamic=False,
        )
        eur = result[result["pydeflate_iso3"] == "EUR"]
        # Unchanged - source aggregate preserved when no member data found
        assert eur[eur["pydeflate_year"] == 2023]["pydeflate_NGDP_D"].iloc[0] == 107.0
