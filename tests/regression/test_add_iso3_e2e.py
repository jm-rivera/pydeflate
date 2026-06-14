"""End-to-end regression test: add_iso3 → imf_gdp_deflate pipeline.

Verifies that the codes produced by add_iso3 are accepted by imf_gdp_deflate
without any extra id_column wiring — the helper writes to "iso_code" (the
deflate default) so both calls compose with no extra args.

The conftest ``mock_source_readers`` autouse fixture stubs the network readers;
no network access is needed.
"""

from __future__ import annotations

import pandas as pd

import pydeflate


def test_add_iso3_feeds_imf_gdp_deflate():
    """add_iso3 produces codes accepted directly by imf_gdp_deflate."""
    # "Atlantis" is confirmed unresolvable by resolvekit (unlike "Narnia" which
    # resolvekit fuzzy-matches to DNK)
    df = pd.DataFrame(
        {
            "country": ["France", "Germany", "European Union", "Atlantis"],
            "year": [2022] * 4,
            "value": [100.0, 200.0, 300.0, 400.0],
        }
    )

    out = pydeflate.add_iso3(df, id_column="country", on_unmatched="warn")

    assert out["iso_code"].iloc[0] == "FRA"
    assert out["iso_code"].iloc[1] == "DEU"
    assert out["iso_code"].iloc[2] == "EU"
    assert pd.isna(out["iso_code"].iloc[3])

    out = out.dropna(subset=["iso_code"])
    assert len(out) == 3

    result = pydeflate.imf_gdp_deflate(
        out,
        base_year=2022,
        source_currency="USA",
        target_currency="USA",
    )

    result_codes = set(result["iso_code"].tolist())
    assert "FRA" in result_codes
    assert "DEU" in result_codes
    # EU is not in the minimal conftest IMF stub (which covers USA/FRA/DEU/GBR/CAN/EMU),
    # so the EU row passes through the outer merge as NaN and this assertion is
    # wiring-only (verifies the code was accepted by the pipeline, not deflated).
    assert "EU" in result_codes

    assert result.loc[result["iso_code"].isin(["FRA", "DEU"]), "value"].notna().all()
