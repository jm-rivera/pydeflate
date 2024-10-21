import pandas as pd

from pydeflate.core.deflator import ExchangeDeflator, PriceDeflator
from pydeflate.core.exchange import Exchange
from pydeflate.core.source import Source, DAC, WorldBank
from pydeflate.pydeflate_config import logger
from pydeflate.sources.common import AvailableDeflators, enforce_pyarrow_types


class BaseDeflate:
    def __init__(
        self,
        deflator_source: Source,
        exchange_source: Source,
        base_year: int,
        price_kind: AvailableDeflators,
        source_currency: str,
        target_currency: str,
        use_source_codes: bool = False,
        to_current: bool = False,
    ):

        self.exchange_rates = Exchange(
            source=exchange_source,
            source_currency=source_currency,
            target_currency=target_currency,
        )

        self.exchange_deflator = ExchangeDeflator(
            source=self.exchange_rates, base_year=base_year
        )

        self.price_deflator = PriceDeflator(
            source=deflator_source, kind=price_kind, base_year=base_year
        )

        self._idx = [
            "pydeflate_year",
            "pydeflate_entity_code" if use_source_codes else "pydeflate_iso3",
        ]

        self.use_source_codes = use_source_codes
        self.to_current = to_current

        self.__post_init__()

    def __post_init__(self):
        data = self._merge_components(
            df=self.price_deflator.deflator_data,
            other=self.exchange_deflator.deflator_data,
        ).pipe(self._merge_components, other=self.exchange_rates.exchange_data)

        # drop where necessary data is missing
        data = data.set_index(self._idx).dropna(how="any").reset_index()

        # Calculate price-exchange deflator
        data["pydeflate_deflator"] = self._calculate_deflator_value(
            data[f"pydeflate_{self.price_deflator.price_kind}"],
            data["pydeflate_EXCHANGE_D"],
            data[f"pydeflate_EXCHANGE"],
        )

        self.pydeflate_data = data

    def _calculate_deflator_value(
        self, price_def: pd.Series, exchange_def: pd.Series, exchange_rate: pd.Series
    ):
        """Calculate the combined deflator value based on the price, exchange,
        and exchange rate. The deflator value is calculated differently based on
        the `to_current` attribute.

        Args:
            price_def (pd.Series): The price deflator.
            exchange_def (pd.Series): The exchange deflator.
            exchange_rate (pd.Series): The exchange rate.

        Returns:
            pd.Series: The deflator value.

        """
        return (
            exchange_def / (price_def * exchange_rate)
            if self.to_current
            else (price_def * exchange_def) / (10_000 * exchange_rate)
        )

    def _merge_components(self, df: pd.DataFrame, other: pd.DataFrame):
        merged = df.merge(other, how="outer", on=self._idx, suffixes=("", "_ex"))
        return merged.drop(columns=merged.filter(regex=f"_ex$").columns, axis=1)

    def _merge_pydeflate_data(
        self,
        data: pd.DataFrame,
        entity_column: str,
        year_column: str,
        year_format: str = "%Y",
    ) -> None:
        """Merge pydeflate's data to the input data based on year and entity.

        Args:
            data (pd.DataFrame): The input DataFrame
            entity_column (str): The column name containing the entity or country codes.
            year_column (str): The column name containing the year information.
            year_format (str, optional): The format of the year (default is '%Y').


        Returns:
            pd.DataFrame: DataFrame with pydeflate data merged to the input data.

        """

        # Convert the year to an integer
        data["pydeflate_year"] = pd.to_datetime(
            data[year_column], format=year_format
        ).dt.year

        # Merge data to the input data based on year and entity
        merged_data = data.merge(
            self.pydeflate_data,
            how="outer",
            left_on=["pydeflate_year", entity_column],
            right_on=self._idx,
            suffixes=("", "_pydeflate"),
            indicator=True,
        ).pipe(enforce_pyarrow_types)

        self._unmatched_data = merged_data.loc[
            merged_data["_merge"] == "left_only"
        ].filter(regex="^(?!pydeflate_)(?!.*_pydeflate$)")

        self._merged_data = (
            merged_data.loc[merged_data["_merge"] != "right_only"]
            .drop(columns="_merge")
            .reset_index(drop=True)
        )

    def _flag_missing_pydeflate_data(self):
        """Flag data which is present in the input data but missing in pydeflate's data."""
        if self._unmatched_data.empty:
            return

        missing = (
            self._unmatched_data.drop_duplicates()
            .dropna(axis=1)
            .drop(columns="_merge")
            .to_string(index=False)
        )

        # log all missing data
        logger.info(f"Missing deflator data for:\n {missing}")

    def deflate(
        self,
        data: pd.DataFrame,
        entity_column: str,
        year_column: str,
        value_column: str,
        target_value_column: str | None = None,
        year_format: str = "%Y",
    ):
        # Make a copy of the input data to avoid modifying the original data
        data = data.copy(deep=True)

        if not target_value_column:
            target_value_column = value_column

        # Keep track of original columns to return data in the same order.
        if target_value_column not in data.columns:
            cols = [*data.columns, target_value_column]
        else:
            cols = df.columns

        # Merge pydeflate data to the input data
        self._merge_pydeflate_data(
            data=data,
            entity_column=entity_column,
            year_column=year_column,
            year_format=year_format,
        )

        # Flag missing data
        self._flag_missing_pydeflate_data()

        # Calculate deflated values
        self._merged_data[target_value_column] = (
            self._merged_data[value_column] / self._merged_data["pydeflate_deflator"]
        ).round(6)

        return self._merged_data[cols]


if __name__ == "__main__":
    ds = DAC()

    base_deflate = BaseDeflate(
        deflator_source=ds,
        exchange_source=ds,
        base_year=2023,
        price_kind="NGDP_D",
        source_currency="LCU",
        target_currency="FRA",
        use_source_codes=False,
        to_current=False,
    )

    df = pd.DataFrame(
        {
            "year": [2022, 2023],
            "entity_code": ["FRA", "FRA"],
            "value": [15228, 14266],
        }
    )

    df = base_deflate.deflate(
        data=df, entity_column="entity_code", year_column="year", value_column="value"
    )
