# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.3.1] - 2025-12-05
### Changed
- Increased minimum `imf-reader` version to 1.4.1 to support the new IMF SDMX API for fetching latest data.

## [2.3.0] - 2025-10-05
### Added
- **Get Deflators Functions**: New functions to retrieve deflator data directly as DataFrames without requiring user data:
  - `get_imf_gdp_deflators()`, `get_imf_cpi_deflators()`, `get_imf_cpi_e_deflators()`
  - `get_wb_gdp_deflators()`, `get_wb_gdp_linked_deflators()`, `get_wb_cpi_deflators()`
  - `get_oecd_dac_deflators()`
- **Get Exchange Rates Functions**: New functions to retrieve exchange rate data directly as DataFrames:
  - `get_imf_exchange_rates()`, `get_wb_exchange_rates()`
  - `get_wb_ppp_rates()`, `get_oecd_dac_exchange_rates()`
- **Flexible Filtering**: All new functions support optional filtering by countries and years via `countries` and `years` parameters.
- **Component Breakdown**: `include_components=True` parameter for deflator functions to retrieve price deflator, exchange deflator, and exchange rate components separately for analysis.

### Changed
- Documentation: Updated README.md with extensive examples of the new get deflator and exchange rate functions.
- Documentation: Added new section "Getting Deflators and Exchange Rates Directly" with common use cases.

### Use Cases
The new functions enable:
- Inspecting and analyzing deflator trends over time
- Pre-computing deflators for custom calculations
- Understanding the components that make up deflators
- Retrieving exchange rates for analysis without converting data

## [2.2.0] - 2025-10-05
### Added
- **Plugin Architecture**: Register custom data sources without modifying pydeflate code via `register_source()`, `get_source()`, `list_sources()`, and `is_source_registered()`.
- **Context Management**: New `PydeflateContext` class and context managers (`pydeflate_session()`, `temporary_context()`) for dependency injection, enabling multiple independent cache directories and thread-safe parallel operations.
- **Exception Hierarchy**: Comprehensive custom exceptions including `PydeflateError` (base), `NetworkError`, `ConfigurationError`, `DataSourceError`, `CacheError`, `MissingDataError`, `SchemaValidationError`, and `PluginError` for fine-grained error handling.
- **Protocol Definitions**: Explicit `SourceProtocol`, `DeflatorProtocol`, and `ExchangeProtocol` interfaces in `protocols.py` for better type safety and extensibility.
- **Schema Validation**: Optional Pandera-based validation for IMF, World Bank, and OECD DAC data sources to catch data quality issues early (enable via `PYDEFLATE_ENABLE_VALIDATION` environment variable or context).
- **Property-Based Testing**: Hypothesis tests verifying mathematical properties (deflation reversibility, exchange rate transitivity, rebasing invariants).
- **Constants Module**: Centralized constants in `constants.py` eliminating magic strings (`PydeflateColumns`, `CurrencyCodes`, `DataSources`, etc.).
- **Enhanced Caching**: New `CacheManager` class with thread-safe file locking via `filelock` and platform-appropriate cache directories via `platformdirs`.
- New dependency: `pandera>=0.20.0` for schema validation.
- New dependency: `platformdirs>=3.0.0` for cross-platform cache directories.
- New dependency: `filelock>=3.15.0` for thread-safe cache operations.
- New dev dependency: `hypothesis>=6.122.3` for property-based testing.

### Fixed
- Corrected `to_current=True` parameter behavior which was resulted in incorrect calculations
in certain edge cases.

### Changed
- **Build System**: Migrated from Poetry to uv for faster dependency resolution and builds.
- **Project Structure**: Adopted src-based layout (`src/pydeflate/` instead of `pydeflate/`) following modern Python packaging best practices.
- **Python Version**: Minimum required version increased from 3.10 to 3.11.
- **Core Architecture**: Rewrote `core/source.py` with cleaner abstractions and improved `Source` class implementation.
- **Source Modules**: Enhanced `sources/common.py`, `sources/dac.py`, `sources/imf.py`, and `sources/world_bank.py` with better error handling and validation.
- **Configuration**: Expanded `pydeflate_config.py` with `set_data_dir()` function; `set_pydeflate_path()` now wraps `set_data_dir()` for backward compatibility.

### Improved
- **Testing Infrastructure**: Reorganized tests into `unit/`, `integration/`, `regression/`, and `property/` directories with comprehensive fixtures in `conftest.py`.
- **Type Safety**: Added type hints throughout the codebase and protocol definitions for better IDE support and static analysis.
- **Error Messages**: More descriptive error messages with source context and actionable guidance.
- **Documentation**: Added advanced usage examples in README covering error handling, plugin system, and context management.
- **Code Quality**: Consistent code formatting and linting with Ruff.

### Removed
- Poetry configuration files (`poetry.lock`, `poetry.toml`).
- Obsolete test files (`tests/test_dac_deflator.py`, `tests/test_dac_totals.py`, `tests/test_wb_ppp_exchange.py`), replaced by improved test suite.

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
