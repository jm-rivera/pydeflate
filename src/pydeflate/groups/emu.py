"""EMU (European Monetary Union) membership tracking.

Tracks which countries are in the eurozone for each year, enabling
GDP-weighted deflator computation with historically accurate membership.
"""

from __future__ import annotations

_EMU_ACCESSION: dict[str, int] = {
    "AUT": 1999,
    "BEL": 1999,
    "DEU": 1999,
    "ESP": 1999,
    "FIN": 1999,
    "FRA": 1999,
    "IRL": 1999,
    "ITA": 1999,
    "LUX": 1999,
    "NLD": 1999,
    "PRT": 1999,
    "GRC": 2001,
    "SVN": 2007,
    "CYP": 2008,
    "MLT": 2008,
    "SVK": 2009,
    "EST": 2011,
    "LVA": 2014,
    "LTU": 2015,
    "HRV": 2023,
}


def members_for_year(year: int) -> list[str]:
    """Return sorted ISO3 codes of countries that were EMU members in the given year."""
    return sorted(
        iso3 for iso3, join_year in _EMU_ACCESSION.items() if join_year <= year
    )


def all_members() -> list[str]:
    """Return all countries that have ever been EMU members."""
    return sorted(_EMU_ACCESSION.keys())


def accession_year(iso3: str) -> int | None:
    """Return the year a country joined the eurozone, or None."""
    return _EMU_ACCESSION.get(iso3)


def is_member(iso3: str, year: int) -> bool:
    """Check if a country was an EMU member in a given year."""
    join_year = _EMU_ACCESSION.get(iso3)
    return join_year is not None and join_year <= year
