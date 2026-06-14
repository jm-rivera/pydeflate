"""Unit tests for pydeflate.convert.add_iso3."""

from __future__ import annotations

import logging

import pandas as pd
import pytest

import pydeflate
from pydeflate.convert import add_iso3
from pydeflate.exceptions import ConfigurationError, UnmatchedEntitiesError


@pytest.fixture()
def propagating_pydeflate_logger():
    """Temporarily enable propagation on the pydeflate logger.

    The production logger sets propagate=False, which prevents pytest's
    caplog fixture (which intercepts via propagation) from capturing log
    records. Flip it for the test duration only.
    """
    logger = logging.getLogger("pydeflate")
    saved = logger.propagate
    logger.propagate = True
    try:
        yield logger
    finally:
        logger.propagate = saved


# ---------------------------------------------------------------------------
# Resolution correctness
# ---------------------------------------------------------------------------


def test_resolves_countries_and_aggregates():
    df = pd.DataFrame({"name": ["France", "European Union", "World"]})

    result = add_iso3(df, "name")

    assert result["iso_code"].tolist() == ["FRA", "EU", "WLD"]


def test_custom_target_column():
    df = pd.DataFrame({"name": ["France"]})

    result = add_iso3(df, "name", target_column="code")

    assert "code" in result.columns
    assert result["code"].tolist() == ["FRA"]


def test_target_column_overwrites_existing():
    df = pd.DataFrame({"name": ["France"], "iso_code": ["OLD"]})

    result = add_iso3(df, "name", target_column="iso_code")

    assert result["iso_code"].tolist() == ["FRA"]


# ---------------------------------------------------------------------------
# Mutation-safety
# ---------------------------------------------------------------------------


def test_does_not_mutate_input():
    df = pd.DataFrame({"name": ["France"]})
    original_columns = set(df.columns)

    add_iso3(df, "name")

    assert set(df.columns) == original_columns


def test_returns_new_dataframe():
    df = pd.DataFrame({"name": ["France"]})

    result = add_iso3(df, "name")

    assert result is not df


# ---------------------------------------------------------------------------
# on_unmatched modes
# ---------------------------------------------------------------------------


def test_warn_sets_na_and_logs(caplog, propagating_pydeflate_logger):
    # "Atlantis" is confirmed unresolvable by resolvekit
    df = pd.DataFrame({"name": ["France", "Atlantis"]})

    with caplog.at_level(logging.WARNING, logger="pydeflate"):
        result = add_iso3(df, "name", on_unmatched="warn")

    assert result["iso_code"].iloc[0] == "FRA"
    assert pd.isna(result["iso_code"].iloc[1])
    assert any("Atlantis" in m for m in caplog.messages)


def test_raise_lists_offending_values():
    # "Atlantis" and "Xyzzy" are confirmed unresolvable by resolvekit
    df = pd.DataFrame({"name": ["France", "Xyzzy", "Atlantis"]})

    with pytest.raises(UnmatchedEntitiesError) as exc_info:
        add_iso3(df, "name", on_unmatched="raise")

    err = exc_info.value
    assert "Atlantis" in err.unmatched
    assert "Xyzzy" in err.unmatched
    # Resolved values must NOT appear in the unmatched list
    assert "France" not in err.unmatched
    assert "FRA" not in err.unmatched
    # Error message also surfaces them
    assert "Atlantis" in str(err)


def test_ignore_silent_na(caplog, propagating_pydeflate_logger):
    # "Atlantis" is confirmed unresolvable by resolvekit
    df = pd.DataFrame({"name": ["France", "Atlantis"]})

    with caplog.at_level(logging.WARNING, logger="pydeflate"):
        result = add_iso3(df, "name", on_unmatched="ignore")

    assert pd.isna(result["iso_code"].iloc[1])
    # No WARNING records should have been emitted
    warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert not warning_records


def test_null_input_cell_is_na_not_unmatched():
    """NaN/None in id_column → pd.NA in target, never triggers raise."""
    df = pd.DataFrame({"name": [None, "France"]})

    # Should not raise even with on_unmatched="raise"
    result = add_iso3(df, "name", on_unmatched="raise")

    assert pd.isna(result["iso_code"].iloc[0])
    assert result["iso_code"].iloc[1] == "FRA"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_dataframe():
    df = pd.DataFrame({"name": pd.Series([], dtype="object")})

    for mode in ("warn", "raise", "ignore"):
        result = add_iso3(df, "name", on_unmatched=mode)
        assert "iso_code" in result.columns
        assert len(result) == 0


def test_all_unmatched_raise():
    # Both names are confirmed unresolvable by resolvekit
    df = pd.DataFrame({"name": ["Xyzzy", "Atlantis"]})

    with pytest.raises(UnmatchedEntitiesError) as exc_info:
        add_iso3(df, "name", on_unmatched="raise")

    assert set(exc_info.value.unmatched) == {"Xyzzy", "Atlantis"}


def test_duplicate_values_resolved_once(monkeypatch):
    """Duplicated names resolve consistently; resolver receives de-duped list."""
    call_args: list[list[str]] = []
    original = pydeflate.convert._match_name_to_iso3

    def tracking_match(to_match):
        call_args.append(list(to_match))
        return original(to_match)

    monkeypatch.setattr("pydeflate.convert._match_name_to_iso3", tracking_match)

    df = pd.DataFrame({"name": ["France", "France", "France"]})
    result = add_iso3(df, "name")

    assert result["iso_code"].tolist() == ["FRA", "FRA", "FRA"]
    # The resolver should have received exactly one unique value
    assert call_args
    assert len(call_args[0]) == 1
    assert call_args[0][0] == "France"


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_missing_id_column_raises_configuration_error():
    df = pd.DataFrame({"name": ["France"]})

    with pytest.raises(ConfigurationError):
        add_iso3(df, "does_not_exist")


def test_invalid_on_unmatched_raises_configuration_error():
    df = pd.DataFrame({"name": ["France"]})

    with pytest.raises(ConfigurationError):
        add_iso3(df, "name", on_unmatched="explode")


# ---------------------------------------------------------------------------
# Public export
# ---------------------------------------------------------------------------


def test_public_export():
    assert hasattr(pydeflate, "add_iso3")
    assert hasattr(pydeflate, "UnmatchedEntitiesError")
    assert "add_iso3" in pydeflate.__all__
    assert "UnmatchedEntitiesError" in pydeflate.__all__
