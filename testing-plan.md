# Testing Overhaul Plan

## Objectives
- Validate pydeflate’s economic transformations (price deflation, currency exchange, PPP conversions) deterministically.
- Guard against regressions in currency aliasing, DAC fallback logic, and data merging quirks.
- Remove network and external service dependencies from the test suite.
- Provide maintainers with fast feedback, clear failure modes, and high-leverage test coverage focused on business rules rather than library mechanics.

## Guiding Principles
- **Deterministic fixtures**: Build tiny, purpose-fit datasets in tests and write them to temporary paths instead of relying on live downloads or large archived files.
- **Layered coverage**: Separate unit-verification of helpers from end-to-end contract tests of the public API wrappers.
- **Regression tracking**: Preserve known bug scenarios as targeted tests referencing the motivating change.
- **Observability**: Assert on both returned data and emitted warnings/logs where behaviour is user-facing (e.g., missing DAC coverage warnings).

## Test Suite Topology
1. `tests/unit/`
   - `test_utils.py`: `merge_user_and_pydeflate_data`, `_use_implied_dac_rates`, `flag_missing_pydeflate_data`, `create_pydeflate_year`.
   - `test_core_deflator.py`: rebasing logic, error paths for missing base-year data, suffix handling.
   - `test_core_exchange.py`: bilateral exchange math, PPP conversion internals, `_convert_exchange` fallbacks.
   - `test_core_api.py`: `_base_operation` directionality, `resolve_common_currencies`, unmatched data handling.
   - `test_sources_common.py`: `compute_exchange_deflator`, column prefix utilities, identifier conversion.

2. `tests/integration/`
   - `test_imf_deflators.py`: GDP/CPI conversions across currencies using IMF fixtures.
   - `test_world_bank_deflators.py`: GDP deflator & linked series, `to_current` flips, ISO3 vs source code joins.
   - `test_dac_deflators.py`: USD↔LCU conversions, DAC implied rates, base-year invariance.
   - `test_exchange_wrappers.py`: `imf_exchange`, `wb_exchange`, `oecd_dac_exchange`, PPP round-trips, reversed exchange flows.
   - Shared fixtures create minimal parquet-like data frames for IMF/WB/DAC and patch reader functions.

3. `tests/regression/`
   - `test_eur_aliases.py`: Ensure `EUR` resolves correctly for IMF/WB sources (fix #26).
   - `test_dac_missing_entities.py`: Validate DAC total fallback with log assertion (bug 2025-02-21).
   - `test_ppp_reverse.py`: Guard PPP reverse conversions (WB PPP helper).

## Fixture Strategy
- `tests/conftest.py`
  - Fixture `temp_data_dir` patches `PYDEFLATE_PATHS.data`/`test_data` to a temporary directory and cleans up after tests.
  - Fixture `sample_source_frames` builds canonical DataFrames (IMF, WB, WB PPP, DAC) with `pydeflate_*` columns, covering multiple currencies (USA, FRA, GBR, CAN, PPP) and years (focus on 2021–2023).
  - Fixture `mock_sources` monkeypatches `pydeflate.sources.{imf,world_bank,dac}` readers to return the sample frames, leaving download functions untouched.
  - Fixture `sample_user_data` exposes small user-facing DataFrames reused across tests.
  - Fixture `caplog_info` configures logging level when verifying log output.

## Coverage Targets & Tooling
- Execute `pytest -q --maxfail=1 --disable-warnings` in CI.
- Enforce `filterwarnings = error` (except for intentional legacy warnings) via `pytest.ini`.
- Aim for ≥90% statement coverage on `pydeflate/core`, `pydeflate/utils`, and `pydeflate/sources/common`.
- Prefer parametrised tests to collapse matrices of currency/flow scenarios.

## Implementation Steps
1. Restructure `tests/` directory and remove legacy fixtures/tests that load live data.
2. Add `conftest.py` and supporting fixture modules.
3. Implement unit tests per module, stubbing data sources as needed.
4. Implement integration suites, ensuring each public API wrapper has at least one deterministic contract test and key permutations (`to_current`, `use_source_codes`, reversed exchange).
5. Capture regression stories with narrow tests referencing historical fixes.
6. Run pytest locally, iterate until green, and update plan & documentation with any deviations discovered during implementation.
7. Keep `testing-plan.md` current if scope changes.

## Risks & Mitigations
- **Fixture Drift**: Overly complex fixtures become hard to maintain → keep sample datasets minimal and documented within fixtures.
- **Performance**: Parametrised tests could balloon runtime → cap dataset size, reuse fixtures, and avoid expensive DataFrame operations in loops.
- **Behavioural Assumptions**: Mocked data may miss edge behaviours → cross-check against documentation and include regression tests for past production bugs.
- **Backward Compatibility**: Legacy `deflate` wrapper remains covered by an integration test path to ensure deprecation messaging still works.

