from pydeflate.core.deflator import ExchangeDeflator, PriceDeflator
from pydeflate.core.exchange import Exchange
from pydeflate.core.source import Source, DAC
from pydeflate.sources.common import AvailableDeflators


class BaseDeflate:
    def __init__(
        self,
        deflator_source: Source,
        exchange_source: Source,
        base_year: int,
        price_kind: AvailableDeflators,
        source_currency: str,
        target_currency: str,
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


if __name__ == "__main__":
    ds = DAC()
    es = DAC()

    bd = BaseDeflate(
        deflator_source=ds,
        exchange_source=es,
        base_year=2010,
        price_kind="NGDP_D",
        source_currency="FRA",
        target_currency="USA",
    )
