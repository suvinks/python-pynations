========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/python-pynations/badge/?style=flat
    :target: https://readthedocs.org/projects/python-pynations
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.org/suvinks/python-pynations.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/suvinks/python-pynations

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/suvinks/python-pynations?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/suvinks/python-pynations

.. |requires| image:: https://requires.io/github/suvinks/python-pynations/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/suvinks/python-pynations/requirements/?branch=master

.. |codecov| image:: https://codecov.io/gh/suvinks/python-pynations/branch/master/graphs/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/suvinks/python-pynations

.. |version| image:: https://img.shields.io/pypi/v/pynations.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/pynations

.. |wheel| image:: https://img.shields.io/pypi/wheel/pynations.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/pynations

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pynations.svg
    :alt: Supported versions
    :target: https://pypi.org/project/pynations

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pynations.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/pynations

.. |commits-since| image:: https://img.shields.io/github/commits-since/suvinks/python-pynations/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/suvinks/python-pynations/compare/v0.0.0...master



.. end-badges

A python library to get information on countries.
The package has functions that enable you to download the datasets from geonames.org and also create sqlite db for the data.

The CountryInfo class allows you to get information of any given country. You can use any common name used for getting data about the country.

* Free software: MIT license

Installation
============

::

    pip install pynations

You can also install the in-development version with::

    pip install https://github.com/suvinks/python-pynations/archive/master.zip


Documentation
=============


https://python-pynations.readthedocs.io/


Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox

References
==========

Data used in this project is downloaded from `Geonames <http://www.geonames.org/>`_ licensed under `Creative Commons 4.0 <https://creativecommons.org/licenses/by/4.0/>`_
