Changelog
=========

1.2.1 (2022-10-28)
------------------
- Fix issues with the change to pathlib.

1.2.0 (2022-10-28)
------------------
- Updated the underlying data
- Added an optional way for users to specify the folder where the data
  should be stored. Use by calling `pydeflate.set_pydeflate_path()'.

1.1.10 (2022-07-28)
------------------
- Fixed the documentation

1.1.9 (2022-07-27)
------------------

- Fixed bugs and added other minor improvements.
- Calling `deflate()` or `exchange()` now creates a deep copy of the
  passed data frame in order to avoid changing the original data/object.
- Re-added a prompt to use `update_all_data()` to manually update the
  underlying data.


1.1.8 (2022-07-26)
------------------

- Fixed bugs and added other minor improvements.
- Improved documentation.


1.1.7 (2022-07-26)
------------------

- Fixed bugs and added other minor improvements.
- Improved documentation.


1.1.6 (2022-07-26)
------------------

- Fixed bugs and added other minor improvements.
- Improved documentation.


1.1.5 (2022-07-26)
------------------

- Fixed bugs and added other minor improvements.
- Improved documentation.

1.1.4 (2022-07-26)
------------------

- Fixed bugs and added other minor improvements.


1.1.3 (2022-07-05)
------------------

- Made significant back-end improvements to how data is managed.
- Improved the deflate API to be more clear about what is needed.
- Fixed small bugs and added other minor improvements.


1.0.1 (2021-11-27)
------------------

- Fixed small bugs and other minor improvements.

1.0.0 (2021-11-27)
------------------

-  Major release.

This is the first major release of pydeflate.

-  This new version effectively breaks any compatibility with previous
   versions of pydeflate.
-  This version is a complete rewrite of the package. Please refer to
   the documentation for information on how pydeflate works
-  The basic functionality of pydeflate can now be considered to be
   settled. Further releases to pydeflate will extend what is possible,
   without altering the basic way in which pydeflate works.

0.1.4 (2021-04-21)
------------------

-  Minor release.

This is a minor update to fix a couple of small errors in doc strings.
It also adds unit testing for updating the underlying data.


0.1.3 (2021-04-21)
------------------

-  Minor release.

This version achieves the basic task at hand. It does not yet have full
testing.



0.1.2 (2021-04-21)
------------------

-  Minor release.

This version achieves the basic task at hand. It does not yet have full
testing.


0.1.1 (2021-04-21)
------------------

-  Minor release.

This version has been yanked.


0.1.0 (2021-04-21)
------------------

-  First release on PyPI.

This version has been yanked.
