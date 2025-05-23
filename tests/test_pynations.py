import pytest
from pynations.CountryInfo import CountryInfo

# It's good practice to ensure data files are built before running tests.
# The CountryInfo constructor handles this, so instantiating it once should suffice
# if there were a global setup. For individual tests, it will be called each time.
# For now, we rely on the constructor.

class TestCountryInfoFeatures:
    def test_country_flag(self):
        """Tests the flag() method for countries with and without defined flags."""
        # Test with a country that has a flag
        c_us = CountryInfo('US')
        assert c_us.flag() == "🇺🇸"

        # Test with a country code not in ISO2_TO_FLAG or a non-existent one
        # Assuming 'XX' is not a real country and not in our ISO2_TO_FLAG map
        c_xx = CountryInfo('XX') # Non-existent or unmapped country
        assert c_xx.flag() == "" 

        # Test with a real country code that is likely not in our small ISO2_TO_FLAG map
        # For example, 'AD' for Andorra, unless it was added to the map.
        # Let's use 'AD' as an example of a real country not in the example map.
        c_ad = CountryInfo('AD')
        # If 'AD' is not in ISO2_TO_FLAG, its flag should be an empty string.
        # This depends on the current state of ISO2_TO_FLAG in CountryInfo.py
        if 'AD' not in CountryInfo('AD').ISO2_TO_FLAG: # Accessing the class attribute for check
             assert c_ad.flag() == ""
        # If it IS in the map, this part of the test would need adjustment or a different country code.

    def test_country_major_cities(self):
        """Tests the major_cities() method."""
        c_us = CountryInfo('US')
        assert isinstance(c_us.major_cities(), list)
        # Assuming US has major cities in the database.
        # This assertion might be too strong if the test DB is empty or minimal for US.
        # A safer bet for a large country:
        assert len(c_us.major_cities()) > 0 
        # Example: Check for a specific city if data consistency is guaranteed.
        # For now, checking for non-emptiness is more robust.
        # if c_us.major_cities(): # Check if list is not empty
        #     assert "New York" in c_us.major_cities() # This is data-dependent

        # Test with a very small country, e.g., Vatican City ('VA')
        # Vatican City might not have 'P' (populated place) entries classified as major cities
        # or its population might be too low to appear in a top 5 list.
        c_va = CountryInfo('VA')
        assert isinstance(c_va.major_cities(), list)
        # It's plausible for Vatican City to have an empty list of major cities
        # depending on Geonames data and our query logic (e.g. population thresholds).
        # So, we just check if it's a list, empty or not.

    def test_country_info_structure_with_new_fields(self):
        """Ensures 'MajorCities' and 'Flag' keys are in the c.info() dictionary."""
        c_de = CountryInfo('DE') # Using Germany as an example
        country_data = c_de.info()
        
        assert country_data is not None # Ensure some data was loaded
        assert 'MajorCities' in country_data
        assert 'Flag' in country_data
        
        # Also check the type of these fields
        assert isinstance(country_data['MajorCities'], list)
        assert isinstance(country_data['Flag'], str)

from unittest.mock import patch, MagicMock
import pynations.CountryInfo # To reset module-level caches

class TestCountryInfoCaching:
    def setUp(self):
        # Reset global caches in pynations.CountryInfo before each test
        pynations.CountryInfo._cached_country_lookup = None
        pynations.CountryInfo._cached_country_info = None

        # Mock build_CountryInfo to prevent actual file I/O and building logic,
        # simulating that files exist and build_CountryInfo returns quickly.
        # This helps isolate testing of caching logic in __init__ and all().
        self.patcher_build_info = patch('pynations.CountryInfo.build_CountryInfo', return_value=True)
        self.mock_build_info = self.patcher_build_info.start()

    def tearDown(self):
        self.patcher_build_info.stop()

    @patch('json.load')
    def test_caching_for_country_info_instantiation(self, mock_json_load):
        """Tests that JSON files are loaded only on first instantiation for different countries."""
        # Arrange: setUp resets caches and mocks build_CountryInfo.
        # We need to provide a plausible return value for json.load if it's called.
        # For lookup, a dict; for country_info, a dict of dicts.
        # Let's make it simple:
        mock_json_load.side_effect = [
            {'us': 123, 'ca': 456}, # Mocked content for countrylookup.json
            {'123': {"Country": "USA"}, '456': {"Country": "Canada"}}  # Mocked content for countryinfo.json
        ]

        # Act 1: Instantiate for 'US'.
        CountryInfo('US')
        
        # Assert 1: json.load called twice (once for lookup, once for info)
        assert mock_json_load.call_count == 2, "json.load should be called for lookup and info files on first access."

        # Act 2: Reset mock and instantiate for 'CA'.
        mock_json_load.reset_mock()
        # Re-apply side_effect if needed for subsequent distinct calls, but here we expect 0 calls.
        
        CountryInfo('CA') # Should use cached lookup and cached country_info

        # Assert 2: json.load should NOT be called again.
        assert mock_json_load.call_count == 0, "json.load should not be called for subsequent accesses if data is cached."

    @patch('json.load')
    def test_caching_for_all_method(self, mock_json_load):
        """Tests that JSON file for all country data is loaded only on the first call to all()."""
        # Arrange: setUp resets caches and mocks build_CountryInfo.
        # Mock return value for countryinfo.json
        mock_json_load.return_value = {"1": {"Country": "Country1"}, "2": {"Country": "Country2"}}

        # Act 1: Call all() for the first time.
        CountryInfo().all()

        # Assert 1: json.load should be called once (for countryinfo.json).
        # build_CountryInfo is mocked, so it won't load.
        # __init__ of CountryInfo() (with no args) doesn't load country_info itself.
        # So, the first all() call should load countryinfo.json.
        assert mock_json_load.call_count == 1, "json.load should be called once for countryinfo.json on first all() call."

        # Act 2: Reset mock and call all() again.
        mock_json_load.reset_mock()
        CountryInfo().all()

        # Assert 2: json.load should NOT be called again.
        assert mock_json_load.call_count == 0, "json.load should not be called on subsequent all() calls if data is cached."
