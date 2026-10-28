import logging

import pandas as pd

from pydeflate import oecd_dac_deflate


def _dac_lookup(frame):
    pdf = frame
    return {
        (row.pydeflate_iso3, row.pydeflate_year): row.pydeflate_NGDP_D
        / (row.pydeflate_EXCHANGE_D * row.pydeflate_EXCHANGE)
        for row in pdf.itertuples()
    }


def test_dac_deflate_uses_aggregate_for_missing_entities(sample_source_frames, caplog):
    data = pd.DataFrame(
        {
            "donor_code": ["999"],
            "year": [2022],
            "value": [300.0],
        }
    )

    with caplog.at_level(logging.INFO, logger="pydeflate"):
        result = oecd_dac_deflate(
            data=data.copy(),
            base_year=2022,
            id_column="donor_code",
            use_source_codes=True,
        )

    messages = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "Using DAC members' rates" in messages
    assert "999: 2022" in messages
    # Fallback to DAC aggregate rates should produce a deflated value, not NaN.
    assert not result["value"].isna().iloc[0]
    assert data.loc[0, "value"] == 300.0
