# Changelog

## 1.3.1 (2023-02-20)
- Updated requirements.

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
