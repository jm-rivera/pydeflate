#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import datetime

import pandas as pd
import requests

from pydeflate.config import paths
from pydeflate.utils import base_year, oecd_codes, value_index, update_update_date

import warnings

warnings.simplefilter("ignore", Warning, lineno=1013)


def _get_zip(url: str) -> requests.models.Response:
    """Download Zip File"""
    try:
        response = requests.get(url)
        response.raise_for_status()

        return response
    except Exception:
        try:
            response = requests.get(url, verify=False)
            return response

        except:
            raise ConnectionError("Could not download ZIP")


def _oecd_bulk_download(url: str, file_name: str) -> pd.DataFrame:
    """Download zip file from bulk download website"""

    import io
    import zipfile as z

    import requests
    from bs4 import BeautifulSoup as bs

    try:
        response = requests.get(url)
    except Exception:
        response = requests.get(url, verify=False)

    soup = bs(response.text, "html.parser")
    link = list(soup.find_all("a"))[0].attrs["onclick"][15:-3].replace("_", "-")
    link = "https://stats.oecd.org/FileView2.aspx?IDFile=" + link

    file = z.ZipFile(io.BytesIO(_get_zip(link).content))

    try:
        df = pd.read_csv(
            file.open(file_name),
            sep=",",
            encoding="ISO-8859-1",
            low_memory=False,
        )

    except:
        df = pd.read_csv(
            file.open(file_name),
            sep="|",
            encoding="ISO-8859-1",
            low_memory=False,
        )

    return df


def _update_dac_deflators() -> None:

    """Update DAC deflators data to latest base year"""

    year = datetime.datetime.now().year

    t = True

    while t:
        url = (
            f"https://www.oecd.org/dac/financing-sustainable-development/"
            f"development-finance-data/Deflators-base-{year}.xls"
        )

        try:
            try:
                df = pd.read_excel(url, header=2)
            except ImportError:
                raise Exception("Could not download data")

            df = df.dropna(how="all")
            df.to_csv(paths.data + r"/dac_deflators.csv", index=False)
            print(f"Updated OECD DAC deflators {year}")
            update_update_date("oecd_dac_deflator")
            t = False

        except:
            year = year - 1


def _update_dac_exchange() -> None:
    """Update DAC Exchange rates to latest available"""

    try:
        exchange = (
            "https://www.oecd.org/dac/financing-sustainable-development/"
            "development-finance-data/Exchange-rates.xls"
        )

        df = pd.read_excel(exchange, header=2)
        df.to_csv(paths.data + r"/dac_exchange_rates.csv", index=False)
        print("Updated OECD DAC exchange rates")
        update_update_date("oecd_dac_exchange")

    except:
        print("Error downloading new exchange rates")


def _clean_dac1(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DAC1 to keep only relevant information for deflators and exchange"""

    cols = {
        "DONOR": "donor_code",
        "AMOUNTTYPE": "type",
        "AIDTYPE": "aid",
        "Year": "year",
        "FLOWS": "flow",
        "Value": "value",
    }

    return (
        df.filter(cols.keys(), axis=1)
        .rename(columns=cols)
        .loc[lambda d: d.aid == 1010]  # only Total ODA
        .loc[lambda d: d.flow == 1140]  # only net disbursements
        .filter(["donor_code", "type", "year", "value"])
        .pivot(index=["donor_code", "year"], columns=["type"], values="value")
        .reset_index()
        .assign(
            exchange=lambda d: d.N / d.A,
            deflator=lambda d: (100 * d.A / d.D).round(2),
            iso_code=lambda d: d.donor_code.map(oecd_codes),
            year=lambda d: pd.to_datetime(d.year, format="%Y"),
        )
        .dropna(subset=["iso_code"])
        .filter(["iso_code", "year", "exchange", "deflator"], axis=1)
    )


def _update_dac1() -> None:
    """Update dac1 data from OECD site and save as feather"""

    url = "https://stats.oecd.org/DownloadFiles.aspx?DatasetCode=TABLE1"
    file_name = "Table1_Data.csv"

    try:
        print("Downloading DAC1 data, which may take a bit")
        df = _oecd_bulk_download(url, file_name).pipe(_clean_dac1)
        df.to_feather(paths.data + r"/dac1.feather")
        print("Sucessfully downloaded DAC1 data")
        update_update_date("oecd_dac_data")
    except:
        raise ConnectionError("Could not download data")


def _read_dac1() -> pd.DataFrame:
    """Read the dac1 file with exchange rates and deflators"""
    return pd.read_feather(paths.data + r"/dac1.feather")


def get_usd_exchange() -> pd.DataFrame:
    """Get the USD exchange rates used by the OECD"""

    df = _read_dac1()

    return df[["iso_code", "year", "exchange"]].rename(columns={"exchange": "value"})


def get_exchange2usd_dict(currency_iso: str) -> dict:
    """Dictionary of currency_iso to USD"""

    df = get_usd_exchange()

    return (
        df.loc[df.iso_code == currency_iso]
        .dropna()
        .set_index("year")["value"]
        .to_dict()
    )


def get_exchange_rate(currency_iso: str) -> dict:
    """Get an exchange rate for a given ISO"""

    df = get_usd_exchange()

    target_xe = get_exchange2usd_dict(currency_iso)

    df.value = df.value / df.year.map(target_xe)

    return df


def get_dac_deflator() -> pd.DataFrame:
    """Get the deflator used by the OECD"""

    df = _read_dac1()

    return df[["iso_code", "year", "deflator"]].rename(columns={"deflator": "value"})


def get_xe_deflator(currency_iso: str) -> pd.DataFrame:
    """get exchange rate deflator based on OECD base year and exchange rates"""

    # get exchange rates
    xe = get_exchange_rate(currency_iso)

    # If currency is not valid
    if int(xe.value.sum()) == 0:
        raise ValueError(f"No currency exchange data for {currency_iso}")

    # get deflators and base year
    defl = get_dac_deflator()

    base = base_year(defl, "year")

    # get the exchange rate as an index based on the base year
    xe.value = value_index(xe, base)

    return xe


def get_gdp_deflator() -> pd.DataFrame:
    """Deduce prices deflator based on exchange rate deflators and DAC
    deflators data"""

    dac_deflator = get_dac_deflator()
    xe_deflator = get_xe_deflator(currency_iso="USA")

    df = dac_deflator.merge(
        xe_deflator,
        on=["iso_code", "year"],
        how="left",
        suffixes=("_def", "_xe"),
    )

    df["value"] = round(df.value_def * (df.value_xe / 100), 3)

    return df[["iso_code", "year", "value"]]
