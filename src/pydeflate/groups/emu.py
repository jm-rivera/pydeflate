"""EMU (European Monetary Union) membership tracking.

Queries resolvekit's Eurozone group as the single source of truth, enabling
GDP-weighted deflator computation with historically accurate membership and
automatic pickup of future accessions.
"""

from __future__ import annotations

import functools

from pydeflate.sources.common import _get_resolver


@functools.cache
def members_for_year(year: int) -> list[str]:
    """Return sorted ISO3 codes of countries that were EMU members in the given year.

    The returned list is cached and shared across calls — callers must not mutate it.
    """
    got = _get_resolver().members_of("Eurozone", as_of=f"{year}-12-31", as_codes="iso3")
    # Defensive: current resolvekit (0.1.11) omits members lacking an iso3 code
    # rather than returning None, so this filter is a no-op today; it guards
    # the list[str] contract against a future resolvekit behavior change.
    return sorted(iso3 for iso3 in got if iso3 is not None)


def all_members() -> list[str]:
    """Return all countries that have ever been EMU members."""
    # 9999 sentinel → as_of="9999-12-31" = all-time membership (no country has
    # ever left the eurozone, so this equals today's set plus any future-dated
    # accession already in the data).
    return members_for_year(9999)


@functools.cache
def is_member(iso3: str, year: int) -> bool:
    """Check if a country was an EMU member in a given year."""
    return iso3 in members_for_year(year)
