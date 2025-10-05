import logging
import pandas as pd

from pydeflate import oecd_dac_deflate
from pydeflate.pydeflate_config import logger as pydeflate_logger


def _dac_lookup(frame):
    pdf = frame
    return {
        (row.pydeflate_iso3, row.pydeflate_year): row.pydeflate_NGDP_D
        / (row.pydeflate_EXCHANGE_D * row.pydeflate_EXCHANGE)
        for row in pdf.itertuples()
    }


def test_dac_deflate_uses_aggregate_for_missing_entities(sample_source_frames):
    data = pd.DataFrame(
        {
            "donor_code": ["999"],
            "year": [2022],
            "value": [300.0],
        }
    )

    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _Capture(level=logging.INFO)
    pydeflate_logger.addHandler(handler)
    try:
        result = oecd_dac_deflate(
            data=data.copy(),
            base_year=2022,
            id_column="donor_code",
            use_source_codes=True,
        )
    finally:
        pydeflate_logger.removeHandler(handler)

    messages = "\n".join(rec.getMessage() for rec in records)
    assert "Using DAC members' rates" in messages
    assert "999: 2022" in messages
    # When data remains unavailable even after fallback, result is NA but input untouched.
    assert result["value"].isna().iloc[0]
    assert data.loc[0, "value"] == 300.0
