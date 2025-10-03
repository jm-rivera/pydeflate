# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.3] - 2025-06-03
### Fixed
- Accept the `EUR` convenience mapping for IMF and World Bank sources.

## [2.1.2] - 2025-04-21
### Fixed
- Handle the `hdx-python-country` breaking change that caused certain country lists to fail.

## [2.1.1] - 2025-02-21
### Fixed
- Ensure DAC entities without dedicated deflators fallback to DAC totals as intended.

## [2.1.0] - 2024-11-18
### Added
- Tooling to convert figures to current PPP using World Bank data.
### Changed
- Improved logging around missing data warnings.

## [2.0.2] - 2024-11-16
### Fixed
- Corrected conversions from current USD to non-USD constant figures.

## [2.0.1] - 2024-11-10
### Fixed
- Corrected handling of non-USD constant figures.

## [2.0.0] - 2024-11-10
### Added
- Source-specific deflator functions such as `imf_gdp_deflate`, `wb_gdp_deflate`, and `oecd_dac_deflate`.
- Source-specific exchange helpers including `imf_exchange` and `oecd_dac_exchange`.
- Support for source-specific country codes through the `use_source_codes` parameter.
### Changed
- Streamlined DataFrame requirements by standardising `id_column`, `year_column`, and `value_column` expectations.
### Deprecated
- Marked the generic `deflate` function for removal in a future release.

## [1.4.2] - 2024-06-28
### Changed
- Upgraded `oda_reader` to align with the latest OECD donor code schema.

## [1.4.1] - 2024-05-07
### Fixed
- Resolved a bug when reading exchange rate data.

## [1.4.0] - 2024-05-06
### Changed
- Adopted the reworked `oda_reader` integration for faster OECD DAC ingestion.
- Ensured freshly downloaded files load automatically.

## [1.3.13] - 2024-04-29
### Changed
- Updated project dependencies.

## [1.3.12] - 2024-03-14
### Fixed
- Addressed the OECD bulk download format change.

## [1.3.11] - 2024-02-29
### Changed
- Updated project dependencies.

## [1.3.9] - 2023-12-11
### Changed
- Updated project dependencies.

## [1.3.8] - 2023-07-06
### Changed
- Updated project dependencies.

## [1.3.7] - 2023-06-12
### Changed
- Updated requirements in response to OECD file encoding changes.
### Fixed
- Corrected handling of new OECD file encodings.

## [1.3.6] - 2023-05-23
### Fixed
- Allowed additional date column formats.
### Changed
- Updated project dependencies.

## [1.3.5] - 2023-04-13
### Fixed
- Handled preliminary OECD data releases that mix base years.
### Changed
- Updated project dependencies.

## [1.3.4] - 2023-02-20
### Changed
- Updated project dependencies.
### Fixed
- Resolved issues when downloading World Bank data.

## [1.3.0] - 2023-02-19
### Changed
- Rebuilt the core logic, data management tools, and tests.
- Updated the APIs for `deflate` and `exchange` to provide clearer parameter naming while keeping backward compatibility with warnings.
### Added
- IMF exchange rate coverage for future GDP projections.
- `pydeflate.set_pydeflate_path()` for configuring local data storage.
- Ability to mix-and-match deflator and exchange rate sources.

## [1.2.10] - 2023-01-12
### Changed
- Updated project dependencies.

## [1.2.9] - 2022-12-21
### Changed
- Improved DAC total deflator handling to reflect dataset values even when published figures differ.

## [1.2.7] - 2022-12-20
### Changed
- Updated project dependencies.

## [1.2.6] - 2022-12-11
### Changed
- Reverted the OECD deflator precision tweak.
### Fixed
- Prevented failures when saving DAC1 feather data.

## [1.2.5] - 2022-12-11
### Changed
- Updated project dependencies.

## [1.2.3] - 2022-11-23
### Changed
- Aligned DAC deflator and exchange rate precision with OECD publications.

## [1.2.2] - 2022-11-03
### Fixed
- Replaced incorrect `pd.NA` usage with `np.nan` when mass replacements occurred.

## [1.2.1] - 2022-10-28
### Fixed
- Addressed regressions introduced during the move to `pathlib`.

## [1.2.0] - 2022-10-28
### Changed
- Refreshed the bundled datasets.
### Added
- Optional configuration for users to set a data storage folder via `pydeflate.set_pydeflate_path()`.

## [1.1.10] - 2022-07-28
### Fixed
- Corrected documentation.

## [1.1.9] - 2022-07-27
### Changed
- Encouraged the use of `update_all_data()` for manual data refreshes.
- Ensured `deflate()` and `exchange()` operate on deep copies of input DataFrames.
- Addressed assorted bugs and minor improvements.

## [1.1.8] - 2022-07-26
### Changed
- Improved documentation.
- Addressed assorted bugs and minor improvements.

## [1.1.7] - 2022-07-26
### Changed
- Improved documentation.
- Addressed assorted bugs and minor improvements.

## [1.1.6] - 2022-07-26
### Changed
- Improved documentation.
- Addressed assorted bugs and minor improvements.

## [1.1.5] - 2022-07-26
### Changed
- Improved documentation.
- Addressed assorted bugs and minor improvements.

## [1.1.4] - 2022-07-26
### Changed
- Addressed assorted bugs and minor improvements.

## [1.1.3] - 2022-07-05
### Changed
- Delivered major internal improvements to data management and the `deflate` API.
- Addressed assorted bugs and minor improvements.

## [1.0.1] - 2021-11-27
### Changed
- Addressed assorted bugs and minor improvements.

## [1.0.0] - 2021-11-27
### Added
- Initial stable release of pydeflate after a complete rewrite.
### Changed
- Established the modern API and broke compatibility with earlier prototypes.

## [0.1.4] - 2021-04-21
### Fixed
- Corrected documentation string errors.
### Added
- Unit testing coverage for updating the underlying data.

## [0.1.3] - 2021-04-21
### Added
- Extended functionality to cover the core use case (limited testing).

## [0.1.2] - 2021-04-21
### Added
- Extended functionality to cover the core use case (limited testing).

## [0.1.1] - 2021-04-21
### Deprecated
- Yanked from distribution.

## [0.1.0] - 2021-04-21
### Added
- First public release on PyPI (later yanked).
