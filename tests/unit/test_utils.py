import logging
import pandas as pd
import pytest

from pydeflate.utils import (
    create_pydeflate_year,
    flag_missing_pydeflate_data,
    get_matched_pydeflate_data,
    get_unmatched_pydeflate_data,
    merge_user_and_pydeflate_data,
)
from pydeflate.pydeflate_config import logger as pydeflate_logger


def test_create_pydeflate_year_handles_string_dates():
    raw = pd.DataFrame({"year": ["2021", "2023"], "value": [1, 2]})

    converted = create_pydeflate_year(raw, year_column="year", year_format="%Y")

    assert list(converted["pydeflate_year"]) == [2021, 2023]
    assert "pydeflate_year" not in raw.columns  # original left untouched


def test_merge_user_and_pydeflate_data_matches_iso_codes():
    user = pd.DataFrame(
        {
            "pydeflate_year": [2022, 2023],
            "iso_code": ["USA", "FRA"],
            "value": [100.0, 200.0],
        }
    )
    pydeflate_data = pd.DataFrame(
        {
            "pydeflate_year": [2022, 2023],
            "pydeflate_iso3": ["USA", "FRA"],
            "pydeflate_entity_code": ["001", "250"],
            "pydeflate_NGDP_D": [100.0, 108.0],
        }
    )

    merged = merge_user_and_pydeflate_data(
        data=user,
        pydeflate_data=pydeflate_data,
        entity_column="iso_code",
        ix=["pydeflate_year", "pydeflate_iso3"],
        source_codes=False,
    )

    matched = get_matched_pydeflate_data(merged)
    assert len(matched) == 2
    assert set(matched.columns) > {"value", "pydeflate_NGDP_D"}

    unmatched = get_unmatched_pydeflate_data(merged)
    assert unmatched.empty


def test_merge_user_and_pydeflate_data_applies_dac_fallback():
    user = pd.DataFrame(
        {
            "pydeflate_year": [2022],
            "donor_code": ["999"],
            "value": [500.0],
        }
    )
    pydeflate_data = pd.DataFrame(
        {
            "pydeflate_year": [2022],
            "pydeflate_entity_code": ["20001"],
            "pydeflate_iso3": ["DAC"],
            "pydeflate_NGDP_D": [100.0],
        }
    )

    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _Capture(level=logging.INFO)
    pydeflate_logger.addHandler(handler)
    try:
        merge_user_and_pydeflate_data(
            data=user,
            pydeflate_data=pydeflate_data,
            entity_column="donor_code",
            ix=["pydeflate_year", "pydeflate_entity_code"],
            source_codes=True,
            dac=True,
        )
    finally:
        pydeflate_logger.removeHandler(handler)

    messages = "\n".join(r.getMessage() for r in records)
    assert "Using DAC members' rates" in messages


def test_flag_missing_pydeflate_data_logs_when_required():
    unmatched = pd.DataFrame(
        {
            "iso_code": ["USA", "USA"],
            "year": [2021, 2023],
        }
    )

    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _Capture(level=logging.INFO)
    pydeflate_logger.addHandler(handler)
    try:
        flag_missing_pydeflate_data(
            unmatched_data=unmatched,
            entity_column="iso_code",
            year_column="year",
        )
    finally:
        pydeflate_logger.removeHandler(handler)

    messages = "\n".join(r.getMessage() for r in records)
    assert "Missing exchange data" in messages
    assert "USA" in messages


def test_get_unmatched_pydeflate_data_filters_indicator_column():
    merged = pd.DataFrame(
        {
            "iso_code": ["USA", "FRA"],
            "pydeflate_year": [2022, 2023],
            "_merge": ["left_only", "both"],
        }
    )

    unmatched = get_unmatched_pydeflate_data(merged)
    expected = pd.DataFrame({"iso_code": ["USA"], "_merge": ["left_only"]})
    assert unmatched.reset_index(drop=True).equals(expected)
