from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from oda_reader import ScannedTable

from pydeflate.cache.manager import BulkCacheManager
from pydeflate.sources import dac, imf, world_bank

# Bound at import: the autouse source fixture replaces dac.read_dac with a stub.
READ_DAC = dac.read_dac


def _imf_sample_frame():
    rows = []
    for concept, values in {
        "NGDPD": [10.0, 12.0],
        "NGDP": [15.0, 18.0],
        "NGDP_D": [98.0, 100.0],
        "PCPI": [99.0, 101.0],
        "PCPIE": [100.0, 102.0],
    }.items():
        for year, value in zip([2021, 2022], values, strict=False):
            rows.append(
                {
                    "CONCEPT_CODE": concept,
                    "OBS_VALUE": value,
                    "SCALE_CODE": 1,
                    "REF_AREA_CODE": "USA",
                    "REF_AREA_LABEL": "United States",
                    "LASTACTUALDATE": "2024-01-01",
                    "TIME_PERIOD": year,
                }
            )
    return pd.DataFrame(rows)


def test_download_weo_generates_parquet(monkeypatch, tmp_path):
    monkeypatch.setattr(imf.weo, "fetch_data", _imf_sample_frame)
    output = tmp_path / "weo.parquet"

    imf._download_weo(output)

    df = pd.read_parquet(output)
    assert {"pydeflate_iso3", "pydeflate_NGDP_D", "pydeflate_EXCHANGE"}.issubset(
        df.columns
    )


def _world_bank_indicator(name: str) -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "year": [2021, 2022],
            "entity_code": ["USA", "CAN"],
            "entity": ["United States", "Canada"],
            name: [100.0, 105.0],
        }
    )
    return data.set_index(["year", "entity_code", "entity"])


def test_download_world_bank_dataset(monkeypatch, tmp_path):
    def fake_parallel(indicators):
        return [_world_bank_indicator(code) for code in indicators.values()]

    monkeypatch.setattr(world_bank, "_parallel_download_indicators", fake_parallel)
    output = tmp_path / "wb.parquet"

    world_bank._download_wb_dataset(world_bank._INDICATORS, output)
    df = pd.read_parquet(output)
    assert "pydeflate_iso3" in df.columns
    assert df["pydeflate_iso3"].isin(["USA", "CAN"]).all()


def test_download_world_bank_dataset_with_ppp(monkeypatch, tmp_path):
    def fake_parallel(indicators):
        return [_world_bank_indicator(code) for code in indicators.values()]

    monkeypatch.setattr(world_bank, "_parallel_download_indicators", fake_parallel)
    output = tmp_path / "wb_lcu_ppp.parquet"

    world_bank._download_wb_dataset(
        world_bank._INDICATORS_LCU_PPP, output, add_ppp_exchange=True
    )
    df = pd.read_parquet(output)
    assert "pydeflate_iso3" in df.columns
    assert "PPP" in df["pydeflate_iso3"].unique()


def _dac_sample_frame():
    return pd.DataFrame(
        {
            "year": [2016, 2016, 2016, 2017, 2017, 2017],
            "aidtype_code": [1010, 1010, 1010, 1010, 1010, 1010],
            "flows_code": [1140, 1140, 1140, 1140, 1140, 1140],
            "donor_code": [1, 1, 1, 1, 1, 1],
            "donor_name": ["Donor", "Donor", "Donor", "Donor", "Donor", "Donor"],
            "amounttype_code": ["A", "N", "D", "A", "N", "D"],
            "value": [100.0, 110.0, 100.0, 100.0, 120.0, 95.0],
        }
    )


def _patch_scan(monkeypatch, tmp_path, rows: pd.DataFrame) -> list[dict]:
    """Make dac.scan("dac1") return *rows* as a Parquet table.

    Returns the list each call's keyword arguments are appended to.
    """
    path = tmp_path / "dac1.parquet"
    rows.to_parquet(path, index=False)
    table = ScannedTable(
        path=path,
        release="etag-1",
        label_release=None,
        downloaded=datetime(2026, 10, 27, tzinfo=UTC),
        columns=tuple(rows.columns),
    )
    calls: list[dict] = []

    def fake_scan(dataset, **kwargs):
        calls.append({"dataset": dataset, **kwargs})
        return table

    monkeypatch.setattr(dac, "scan", fake_scan)
    return calls


def test_download_dac_dataset(monkeypatch, tmp_path):
    _patch_scan(monkeypatch, tmp_path, _dac_sample_frame())
    output = tmp_path / "dac.parquet"

    dac._download_dac(output)
    df = pd.read_parquet(output)
    assert "pydeflate_DAC_DEFLATOR" in df.columns
    assert "pydeflate_iso3" in df.columns
    assert df["pydeflate_EXCHANGE"].tolist() == [1.1, 1.2]


def test_read_dac_downloads_a_fresh_bulk_file_on_rebuild(monkeypatch, tmp_path):
    """A rebuild of the DAC cache, forced or first, refreshes the DAC1 scan."""
    calls = _patch_scan(monkeypatch, tmp_path, _dac_sample_frame())
    manager = BulkCacheManager(tmp_path / "bulk")
    monkeypatch.setattr(dac, "bulk_cache_manager", lambda: manager)

    READ_DAC()
    READ_DAC()
    READ_DAC(update=True)

    assert calls == [{"dataset": "dac1", "refresh": True}] * 2


def test_download_dac_keeps_eu_institutions_euro_rate(monkeypatch, tmp_path):
    """EU Institutions (918) reports N in euros; aggregates publish no N."""
    donors = {
        (918, "EU Institutions"): {"A": 100.0, "N": 95.09, "D": 100.0},
        (20001, "DAC Countries, Total"): {"A": 100.0, "D": 100.0},
        (20003, "G7 Countries, Total"): {"A": 100.0, "D": 100.0},
    }
    raw = pd.DataFrame(
        [
            {
                "year": 2022,
                "aidtype_code": 11010,
                "flows_code": 1160,
                "donor_code": code,
                "donor_name": name,
                "amounttype_code": amount_type,
                "value": value,
            }
            for (code, name), amounts in donors.items()
            for amount_type, value in amounts.items()
        ]
    )
    _patch_scan(monkeypatch, tmp_path, raw)
    output = tmp_path / "dac.parquet"

    dac._download_dac(output)
    table = pd.read_parquet(output).set_index("pydeflate_entity_code")

    assert table["pydeflate_EXCHANGE"].to_dict() == {918: 0.9509, 20001: 1, 20003: 1}
    assert table["pydeflate_iso3"].to_dict() == {
        918: "EUI",
        20001: "DAC",
        20003: "G7C",
    }


def test_download_dac_gives_the_dac_code_to_dac_countries_only(monkeypatch, tmp_path):
    """DAC Members (20000) stays unresolved, so data keyed DAC matches one row."""
    raw = pd.DataFrame(
        [
            {
                "year": 2022,
                "aidtype_code": 11010,
                "flows_code": 1160,
                "donor_code": code,
                "donor_name": name,
                "amounttype_code": amount_type,
                "value": 100.0,
            }
            for code, name, amount_types in [
                (4, "France", "AND"),
                (20000, "DAC Members", "AD"),
                (20001, "DAC countries", "AD"),
            ]
            for amount_type in amount_types
        ]
    )
    _patch_scan(monkeypatch, tmp_path, raw)
    output = tmp_path / "dac.parquet"

    dac._download_dac(output)
    codes = pd.read_parquet(output).set_index("pydeflate_entity_code")["pydeflate_iso3"]

    assert codes[20001] == "DAC"
    assert pd.isna(codes[20000])


def test_pivot_amount_type_creates_columns():
    pivoted = dac._pivot_amount_type(_dac_sample_frame())
    assert {"A", "N", "D"}.issubset(pivoted.columns)


def test_world_bank_read_functions(monkeypatch, tmp_path):
    data = pd.DataFrame({"pydeflate_iso3": ["USA"], "value": [1]})

    class DummyCache:
        def __init__(self, path: Path):
            self.path = path

        def ensure(self, entry, refresh=False):
            data.to_parquet(self.path)
            return self.path

    cache_path = tmp_path / "wb.parquet"
    dummy = DummyCache(cache_path)
    monkeypatch.setattr(world_bank, "bulk_cache_manager", lambda: dummy)

    df = world_bank.read_wb(update=True)
    assert not df.empty

    dummy_lcu = DummyCache(tmp_path / "wb_lcu.parquet")
    monkeypatch.setattr(world_bank, "bulk_cache_manager", lambda: dummy_lcu)
    df = world_bank.read_wb_lcu_ppp(update=False)
    assert not df.empty

    dummy_usd = DummyCache(tmp_path / "wb_usd.parquet")
    monkeypatch.setattr(world_bank, "bulk_cache_manager", lambda: dummy_usd)
    df = world_bank.read_wb_usd_ppp(update=False)
    assert not df.empty
