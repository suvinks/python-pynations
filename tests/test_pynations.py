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
