"""Regression tests for aggregate and country-alias name resolution.

These tests verify the resolvekit migration correctly resolves entity names
(Congo, Korea, Iran, Yemen, Micronesia, Aruba, Taiwan, World, EU entities).
"""

import pandas as pd
import pytest

from pydeflate.sources.common import add_pydeflate_iso3


def _resolve(entity: str) -> object:
    """Return the pydeflate_iso3 value for a single entity name."""
    df = pd.DataFrame({"entity": [entity]})
    return add_pydeflate_iso3(df, column="entity")["pydeflate_iso3"].iloc[0]


# ---------------------------------------------------------------------------
# Primary bug fix: Congo disambiguation (fails on old static map)
# ---------------------------------------------------------------------------


def test_congo_rep_and_dem_rep_resolve_distinctly():
    """Congo, Rep. → COG and Congo, Dem. Rep. → COD (the primary migration fix)."""
    df = pd.DataFrame({"entity": ["Congo, Rep.", "Congo, Dem. Rep."]})
    result = add_pydeflate_iso3(df, column="entity")["pydeflate_iso3"].tolist()

    assert result[0] == "COG", "Congo, Rep. must map to COG (Republic of Congo)"
    assert result[1] == "COD", "Congo, Dem. Rep. must map to COD (DR Congo)"


# ---------------------------------------------------------------------------
# Aggregate / group overrides (via ENTITY_TO_PYDEFLATE dict)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entity, expected",
    [
        ("World", "WLD"),
        ("G7", "G7C"),
        ("Sub-Sahara Africa", "SSA"),
    ],
)
def test_aggregate_entities_resolve(entity, expected):
    """Core aggregate entities map to their pydeflate group codes."""
    assert _resolve(entity) == expected


# ---------------------------------------------------------------------------
# Country aliases previously missing from the static map
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entity, expected",
    [
        ("Korea, Rep.", "KOR"),
        ("Iran", "IRN"),
        ("Yemen", "YEM"),
        ("Micronesia, Fed. Sts.", "FSM"),
        ("Aruba", "ABW"),
        ("Taiwan", "TWN"),
    ],
)
def test_previously_missing_country_aliases(entity, expected):
    """Country aliases that were absent from the old static HDX map now resolve."""
    assert _resolve(entity) == expected


# ---------------------------------------------------------------------------
# Parenthetical / variant strings that IMF-WEO and OECD-DAC actually emit
# (Issue 1 from plan review — confirmed in verification-0.1.10.md addendum)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entity, expected",
    [
        ("European Union (EU)", "EU"),
        ("Euro Area (EA)", "EMU"),
        ("DAC Countries, Total", "DAC"),
        ("Kosovo, Republic of", "XXK"),
    ],
)
def test_parenthetical_variant_strings(entity, expected):
    """Parenthetical/variant forms used by data sources resolve correctly."""
    assert _resolve(entity) == expected


# ---------------------------------------------------------------------------
# Kosovo override: dict beats the iso3 fall-through (XKS → XXK, not XKX)
# ---------------------------------------------------------------------------


def test_kosovo_override_wins_over_iso3_fallthrough():
    """Kosovo maps to XXK (pydeflate policy), not XKX (resolvekit's own iso3)."""
    assert _resolve("Kosovo") == "XXK"


# ---------------------------------------------------------------------------
# Unresolved names → pd.NA (fillna behavior)
# ---------------------------------------------------------------------------


def test_non_dac_countries_is_unresolved():
    """'Non-DAC countries' is unresolved (don't replicate the old ESH bug)."""
    result = _resolve("Non-DAC countries")
    assert pd.isna(result), (
        f"'Non-DAC countries' should be pd.NA, not {result!r} "
        "(D2: do not replicate ESH)"
    )


def test_unknown_entity_is_unresolved():
    """Completely unknown names produce pd.NA via the fillna passthrough."""
    result = _resolve("Not A Country")
    assert pd.isna(result)
