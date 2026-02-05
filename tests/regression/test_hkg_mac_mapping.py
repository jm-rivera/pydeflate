"""Regression test for issue #38.

Hong Kong and Macao SAR entity names from IMF WEO data were fuzzy-matched to
CHN instead of HKG / MAC, causing duplicate rows for China in exchange rate
and deflator outputs.
"""

import pandas as pd

from pydeflate.sources.common import add_pydeflate_iso3


def test_hong_kong_maps_to_hkg_not_chn():
    """Hong Kong SAR must be mapped to HKG, not fuzzy-matched to CHN."""
    df = pd.DataFrame(
        {
            "entity": [
                "China, People's Republic of",
                "Hong Kong Special Administrative Region, People's Republic of China",
            ],
        }
    )

    # Use real fuzzy matching (the bug is in fuzzy matching results)
    result = add_pydeflate_iso3(df, column="entity", from_type="regex")

    iso3_values = result["pydeflate_iso3"].tolist()
    assert iso3_values[0] == "CHN", "Mainland China should map to CHN"
    assert iso3_values[1] == "HKG", "Hong Kong SAR should map to HKG, not CHN"


def test_macao_maps_to_mac_not_chn():
    """Macao SAR must be mapped to MAC, not fuzzy-matched to CHN."""
    df = pd.DataFrame(
        {
            "entity": [
                "China, People's Republic of",
                "Macao Special Administrative Region, People's Republic of China",
            ],
        }
    )

    result = add_pydeflate_iso3(df, column="entity", from_type="regex")

    iso3_values = result["pydeflate_iso3"].tolist()
    assert iso3_values[0] == "CHN", "Mainland China should map to CHN"
    assert iso3_values[1] == "MAC", "Macao SAR should map to MAC, not CHN"


def test_no_duplicate_chn_rows_after_iso3_mapping():
    """After ISO3 mapping, there should be exactly one row per (iso3, year)."""
    df = pd.DataFrame(
        {
            "entity": [
                "China, People's Republic of",
                "Hong Kong Special Administrative Region, People's Republic of China",
                "Macao Special Administrative Region, People's Republic of China",
            ],
            "year": [2022, 2022, 2022],
            "value": [100.0, 200.0, 300.0],
        }
    )

    result = add_pydeflate_iso3(df, column="entity", from_type="regex")

    # Each entity should have a unique ISO3 code
    chn_rows = result[result["pydeflate_iso3"] == "CHN"]
    assert len(chn_rows) == 1, (
        f"Expected 1 CHN row, got {len(chn_rows)} — "
        "HKG/MAC are being fuzzy-matched to CHN"
    )

    # Verify HKG and MAC exist as separate entries
    assert "HKG" in result["pydeflate_iso3"].values, "HKG should be present"
    assert "MAC" in result["pydeflate_iso3"].values, "MAC should be present"
