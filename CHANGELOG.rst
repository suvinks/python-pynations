0.0.3 (YYYY-MM-DD)
------------------

* Added `flag()` method to `CountryInfo` to retrieve a country's flag emoji.
* Added `major_cities()` method to `CountryInfo` to retrieve a list of major cities.
* Updated `build_CountryInfo` to include flag and major city data in `countryinfo.json`.
* Optimized `build_CountryInfo` data generation by improving language data lookups, reducing database queries during this process.
* Ensured and verified that data loading for `CountryInfo` instances and the `all()` method is effectively cached, significantly improving performance for repeated access to country data.
* Added simple benchmarking examples to `CountryInfo.py` to demonstrate caching performance.
* Updated tests to cover new features and caching behavior.
* Enhanced `geodownloader.py` to support parallel downloads for multiple files/countries, speeding up the data acquisition process.
* Refactored data loading logic in `geosqlite.py`: replaced shell command calls (`sed`, `sqlite3 .import`) with Python-native CSV parsing and batch SQLite inserts (`executemany`). This improves performance, error handling, and maintainability of the database setup.
* Removed the use of intermediate temporary files (`quoted.txt`, `temp.txt`) during data loading in `geosqlite.py`, reducing I/O.
* Added basic timing instrumentation to `geodownloader.py` and `geosqlite.py` to display execution time.
* Introduced initial automated tests for `geodownloader.py` and `geosqlite.py` using mocked network calls and dummy data.


Changelog
=========

0.0.2 (2020-04-25)
------------------

* Corrections to solve issues with Windows 10.

0.0.1 (2020-04-25)
------------------

* First release on PyPI.
