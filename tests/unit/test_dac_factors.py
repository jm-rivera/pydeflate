"""get_oecd_dac_conversion_factors on a small DAC1 table in the scan("dac1") layout."""

from datetime import UTC, datetime

import pandas as pd
import pytest
from oda_reader import ScannedTable

from pydeflate import (
    get_oecd_dac_conversion_factors,
    oecd_dac_deflate,
    oecd_dac_exchange,
)
from pydeflate.exceptions import DataSourceError
from pydeflate.sources.dac import dac_source_frame, read_dac1_rows

YEARS = [2016, 2017, 2018, 2019]
BASE_YEAR = 2018

# (code, name): {year: (A, N, D)}. A == D in 2018, the table's price base year.
# France has no 2016 row. DAC aggregates publish no national-currency amount.
DONORS: dict[tuple[int, str], dict[int, tuple[float, float | None, float]]] = {
    (4, "France"): {
        2017: (110.0, 97.0, 108.0),
        2018: (120.0, 102.0, 120.0),
        2019: (125.0, 111.0, 122.0),
    },
    (12, "United Kingdom"): {
        2016: (200.0, 148.0, 190.0),
        2017: (210.0, 163.0, 205.0),
        2018: (220.0, 165.0, 220.0),
        2019: (230.0, 180.0, 226.0),
    },
    (302, "United States"): {
        2016: (300.0, 300.0, 290.0),
        2017: (310.0, 310.0, 305.0),
        2018: (320.0, 320.0, 320.0),
        2019: (330.0, 330.0, 325.0),
    },
    (918, "EU Institutions"): {
        2016: (50.0, 45.2, 48.0),
        2017: (55.0, 48.7, 53.0),
        2018: (60.0, 50.8, 60.0),
        2019: (65.0, 58.1, 64.0),
    },
    (20001, "DAC Countries, Total"): {
        2016: (1000.0, None, 960.0),
        2017: (1050.0, None, 1030.0),
        2018: (1100.0, None, 1100.0),
        2019: (1150.0, None, 1130.0),
    },
}


def _dac1_rows() -> pd.DataFrame:
    rows = []
    for (code, name), years in DONORS.items():
        for year, amounts in years.items():
            # Total ODA: line 1010 net disbursements before 2018, 11010 grant
            # equivalents from 2018. Line 1010 grant equivalents and line 1015
            # rows are decoys the factors must ignore.
            line, flow = (1010, 1140) if year < 2018 else (11010, 1160)
            for amount_type, value in zip("AND", amounts, strict=True):
                if value is None:
                    continue
                base = {
                    "donor_code": code,
                    "donor_name": name,
                    "part_code": 1,
                    "part_name": "Part I",
                    "aid_type": "ODA",
                    "fund_flows": "Flows",
                    "amounttype_code": amount_type,
                    "amount_type": amount_type,
                    "year": year,
                    "flags": None,
                }
                rows.append(
                    base | {"aidtype_code": line, "flows_code": flow, "value": value}
                )
                rows.append(
                    base
                    | {"aidtype_code": 1010, "flows_code": 1160, "value": value + 7}
                )
                rows.append(
                    base
                    | {"aidtype_code": 1015, "flows_code": 1140, "value": value + 11}
                )
    return pd.DataFrame(rows).astype(
        {
            "donor_code": "int32",
            "part_code": "int32",
            "aidtype_code": "int32",
            "flows_code": "int32",
            "year": "int32",
        }
    )


@pytest.fixture
def dac1_path(tmp_path):
    path = tmp_path / "dac1.parquet"
    _dac1_rows().to_parquet(path, index=False)
    return path


@pytest.fixture
def scanned(dac1_path):
    rows = pd.read_parquet(dac1_path)
    return ScannedTable(
        path=dac1_path,
        release='"0x8DF2539D20A32DF"',
        downloaded=datetime(2026, 10, 27, tzinfo=UTC),
        columns=tuple(rows.columns),
    )


@pytest.fixture
def dac_source_from_fixture(dac1_path, monkeypatch):
    """Point today's DAC source (oecd_dac_deflate, oecd_dac_exchange) at the fixture."""
    frame = dac_source_frame(read_dac1_rows(dac1_path))
    monkeypatch.setattr("pydeflate.core.source.read_dac", lambda update=False: frame)


def test_columns_and_release_from_scanned_table(scanned):
    result = get_oecd_dac_conversion_factors(
        scanned, entities=[302, 4], years=[2019, 2018]
    )

    assert result.release == '"0x8DF2539D20A32DF"'
    assert result.factors.dtypes.astype(str).to_dict() == {
        "entity_code": "int64",
        "year": "int64",
        "factor": "float64",
        "fallback": "bool",
    }
    assert result.factors[["entity_code", "year"]].values.tolist() == [
        [4, 2018],
        [4, 2019],
        [302, 2018],
        [302, 2019],
    ]


def test_plain_path_reports_no_release(dac1_path):
    result = get_oecd_dac_conversion_factors(dac1_path, entities=[302], years=[2019])
    assert result.release is None


def test_exchange_factors_use_total_oda_lines(dac1_path):
    """EUR factors are EU Institutions' N/A on the line and flow for each year."""
    factors = get_oecd_dac_conversion_factors(
        dac1_path, entities=[302], years=YEARS, target_currency="EUR"
    ).factors

    expected = [
        round(n / a, 6)
        for a, n, _ in DONORS[(918, "EU Institutions")].values()
        if n is not None
    ]
    assert factors["factor"].tolist() == pytest.approx(expected, abs=1e-12)


def test_missing_entities_fall_back_to_dac_total(dac1_path):
    factors = get_oecd_dac_conversion_factors(
        dac1_path,
        entities=[20001, 20002, 12345, 4],
        years=[2016, 2019, 2030],
        target_currency="GBP",
        base_year=BASE_YEAR,
    ).factors.set_index(["entity_code", "year"])

    assert factors["fallback"].to_dict() == {
        (code, year): code in {20002, 12345}
        for code in [4, 12345, 20001, 20002]
        for year in [2016, 2019, 2030]
    }
    for code in [20002, 12345]:
        for year in [2016, 2019]:
            assert factors.loc[(code, year), "factor"] == pytest.approx(
                factors.loc[(20001, year), "factor"]
            )
    # A year the table lacks, and a year a present entity lacks, stay missing.
    assert factors.xs(2030, level="year")["factor"].isna().all()
    assert pd.isna(factors.loc[(4, 2016), "factor"])
    assert not factors.loc[(4, 2016), "fallback"]


@pytest.mark.parametrize("currency", ["USD", "EUR", "GBP"])
@pytest.mark.parametrize("base_year", [None, BASE_YEAR])
def test_matches_oecd_dac_functions(
    dac1_path, dac_source_from_fixture, currency, base_year
):
    entities = [4, 12, 302, 918, 20001, 20002, 12345]
    data = pd.DataFrame(
        [(code, year, 1000.0) for code in entities for year in YEARS],
        columns=["entity_code", "year", "value"],
    )
    common = {
        "source_currency": "USA",
        "target_currency": currency,
        "id_column": "entity_code",
        "use_source_codes": True,
    }
    if base_year is None:
        expected = oecd_dac_exchange(data, **common)
    else:
        expected = oecd_dac_deflate(data, base_year=base_year, **common)

    factors = get_oecd_dac_conversion_factors(
        dac1_path,
        entities=entities,
        years=YEARS,
        target_currency=currency,
        base_year=base_year,
    ).factors
    merged = expected.merge(factors, on=["entity_code", "year"], validate="1:1")
    converted = merged["value"].astype("float64")

    assert merged["factor"].isna().tolist() == converted.isna().tolist()
    assert merged["factor"].notna().sum() > len(entities)
    assert (merged["factor"] * 1000).tolist() == pytest.approx(
        converted.tolist(), abs=1e-6, nan_ok=True
    )


def test_table_without_dac1_columns_raises(tmp_path):
    path = tmp_path / "other.parquet"
    pd.DataFrame({"donor_code": [4], "year": [2019], "value": [1.0]}).to_parquet(path)

    with pytest.raises(DataSourceError, match="amounttype_code"):
        get_oecd_dac_conversion_factors(path, entities=[4], years=[2019])


def test_base_year_must_be_int(dac1_path):
    with pytest.raises(ValueError, match="base_year"):
        get_oecd_dac_conversion_factors(
            dac1_path,
            entities=[4],
            years=[2019],
            base_year="2018",
        )
