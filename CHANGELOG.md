# Changelog

## v2.1.2(2025-04-21)
Handles a bug with hdx-python-country which makes certain lists fail

## v2.1.1(2025-02-21)
In DAC statistics, the DAC deflators are used for entities which do not have their
own DAC deflator. This patch enforces that behaviour.

## v2.1 (2024-11-18)
**New feature**: added a tool to convert numbers to current PPP, using
World Bank data.
Improved how missing data gets logged.

## v2.0.2 (2024-11-16)
Fixes a bug with current USD to non-USD constant figures.

## v2.0.1 (2024-11-10)
Fixes a bug with non-USD constant figures.

## v2.0.0 (2024-11-10)

🚀 Major Release
- New Function Names and API Structure:
  - Introduced source-specific deflator functions (e.g., imf_gdp_deflate, wb_gdp_deflate, oecd_dac_deflate). 
  - Added source-specific exchange functions for currency conversion (e.g., imf_exchange, oecd_dac_exchange).
- Deprecated deflate function; users are encouraged to transition to new deflator functions. 
- Improved Setup and Data Requirements:
  - Streamlined DataFrame requirements: id_column, year_column, and value_column now required explicitly. 
  - Added use_source_codes parameter to allow for DAC, IMF, and other source-specific country codes.
- And much more. Please see the release documentation or the readme for more details.

## 1.4.2 (2024-06-28)
- Use a later version of oda_reader to deal with a bug found in the new OECD donor 
 code schema.

## 1.4.1 (2024-05-07)
- Fixed a bug in reading the exchange data

## 1.4.0 (2024-05-06)
- Implements a change to the oda_reader package to manage reading the OECD DAC data. There are no changes in terms of usage, but it greatly optimises how data is read. 
- The above change fixes an error where newly downloaded files were not
read automatically

## 1.3.13 (2024-04-29)
- Updated requirements.

## 1.3.12 (2024-03-14)
* Fixed a bug introduced by changes in the OECD bulk download service.

## 1.3.11 (2024-02-29)
- Updated requirements.

## 1.3.9 (2023-12-11)
- Updated requirements.

## 1.3.8 (2023-07-06)
- Updated requirements.

## 1.3.7 (2023-06-12)
- Fixed an issue created by a change in OECD encoding of files
- Updated requirements

## 1.3.6 (2023-05-23)
- Fixed an issue which meant not all date columns were accepted.
- Updated requirements

## 1.3.5 (2023-04-13)
- Fixed an issue created by the preliminary OECD data release which mixes base years
- Updated requirements


## 1.3.4 (2023-02-20)
- Updated requirements.
- Fixed issues with downloading world bank data

## 1.3.0 (2023-02-19)

This release includes a major refactoring/rewriting of the underlying
logic, tools to get and manage the data, and tests.

No breaking changes were introduced, but the API for the `deflate` and `exchange()`
functions has changed. The new API
has more consistent naming and provides additional options. The old API
is still available, but will be deprecated in a future release. Using
the old parameters will raise a warning.

**New features:** 
- Added new exchange rates for the IMF. As a side
effect, deflators can now be calculated for future years for which the
IMF has GDP projections.
-   A data folder can now be specified by calling `pydeflate.set_pydeflate_path()`. This allows
    users to specify where the data should be stored.
-   Users can now specify (and therefore combine) the source of
    deflators and exchange rates.

## 1.2.10 (2023-01-12)

-   Updated requirements.

## 1.2.9 (2022-12-21)

-   Greatly improved how DAC deflators are handled for the "DAC Total"
    grouping. It now tracks the data as used in the database even if the
    published "deflator" figures differ.

## 1.2.7 (2022-12-20)

-   Update requirements.

## 1.2.6 (2022-12-11)

-   Revert change to the precision level of deflators for OECD data.
-   Fix problem when saving dac1 feather.

## 1.2.5 (2022-12-11)

-   Update dependencies

## 1.2.3 (2022-11-23)

\- Reduced the precision level of deflators and exchange rates on DAC
data. This update aligns with the precision level in DAC data, as
published by the OECD.

## 1.2.2 (2022-11-03)

-   Fix issues with <span class="title-ref">pd.NA</span> when too many
    values are replaced. It now uses <span
    class="title-ref">np.nan</span>.

## 1.2.1 (2022-10-28)

-   Fix issues with the change to pathlib.

## 1.2.0 (2022-10-28)

-   Updated the underlying data
-   Added an optional way for users to specify the folder where the data
    should be stored. Use by calling `pydeflate.set_pydeflate_path()`.

## 1.1.10 (2022-07-28)
- Fixed the documentation

## 1.1.9 (2022-07-27)

-   Fixed bugs and added other minor improvements.
-   Calling <span class="title-ref">deflate()</span> or <span
    class="title-ref">exchange()</span> now creates a deep copy of the
    passed data frame in order to avoid changing the original
    data/object.
-   Re-added a prompt to use <span
    class="title-ref">update_all_data()</span> to manually update the
    underlying data.

## 1.1.8 (2022-07-26)

-   Fixed bugs and added other minor improvements.
-   Improved documentation.

## 1.1.7 (2022-07-26)

-   Fixed bugs and added other minor improvements.
-   Improved documentation.

## 1.1.6 (2022-07-26)

-   Fixed bugs and added other minor improvements.
-   Improved documentation.

## 1.1.5 (2022-07-26)

-   Fixed bugs and added other minor improvements.
-   Improved documentation.

## 1.1.4 (2022-07-26)

-   Fixed bugs and added other minor improvements.

## 1.1.3 (2022-07-05)

-   Made significant back-end improvements to how data is managed.
-   Improved the deflate API to be more clear about what is needed.
-   Fixed small bugs and added other minor improvements.

## 1.0.1 (2021-11-27)

-   Fixed small bugs and other minor improvements.

## 1.0.0 (2021-11-27)

-   Major release.

This is the first major release of pydeflate.

-   This new version effectively breaks any compatibility with previous
    versions of pydeflate.
-   This version is a complete rewrite of the package. Please refer to
    the documentation for information on how pydeflate works
-   The basic functionality of pydeflate can now be considered to be
    settled. Further releases to pydeflate will extend what is possible,
    without altering the basic way in which pydeflate works.

## 0.1.4 (2021-04-21)

-   Minor release.

This is a minor update to fix a couple of small errors in doc strings.
It also adds unit testing for updating the underlying data.

## 0.1.3 (2021-04-21)

-   Minor release.

This version achieves the basic task at hand. It does not yet have full
testing.

## 0.1.2 (2021-04-21)

-   Minor release.

This version achieves the basic task at hand. It does not yet have full
testing.

## 0.1.1 (2021-04-21)

-   Minor release.

This version has been yanked.

## 0.1.0 (2021-04-21)

-   First release on PyPI.

This version has been yanked.
