from dataclasses import dataclass


@dataclass
class PydeflateSchema:
    YEAR: str = "year"
    PROVIDER_CODE: str = "oecd_provider_code"
    PROVIDER_NAME: str = "provider"
    AMOUNT_TYPE: str = "amount_type"
    AID_TYPE: str = "aid_type"
    ISO_CODE: str = "iso_code"
    FLOWS: str = "flows"
    VALUE: str = "value"
    USD_COMMITMENT: str = "usd_commitment"
    USD_DISBURSEMENT: str = "usd_disbursement"
    EXCHANGE: str = "exchange"
    EXCHANGE_DEFLATOR: str = "exchange_deflator"
    DEFLATOR: str = "deflator"
    PRICE_DEFLATOR: str = "price_deflator"
    INDICATOR: str = "indicator"


OECD_MAPPING: dict[str, str] = {
    "Year": PydeflateSchema.YEAR,
    "donor_code": PydeflateSchema.PROVIDER_CODE,
    "DONOR": PydeflateSchema.PROVIDER_CODE,
    "AMOUNTTYPE": PydeflateSchema.AMOUNT_TYPE,
    "AIDTYPE": PydeflateSchema.AID_TYPE,
    "FLOWS": PydeflateSchema.FLOWS,
    "Value": PydeflateSchema.VALUE,
    "donor_name": PydeflateSchema.PROVIDER_NAME,
    "provider": PydeflateSchema.PROVIDER_NAME,
    "provider_code": PydeflateSchema.PROVIDER_CODE,
    "usd_commitment": PydeflateSchema.USD_COMMITMENT,
    "usd_disbursement": PydeflateSchema.USD_DISBURSEMENT,
}
