"""
Entrypoint module, in case you use `python -mpynations`.


Why does this file exist, and why __main__? For more info, read:

- https://www.python.org/dev/peps/pep-0338/
- https://docs.python.org/2/using/cmdline.html#cmdoption-m
- https://docs.python.org/3/using/cmdline.html#cmdoption-m
"""
from pynations.CountryInfo import CountryInfo
import json # Added for pretty printing

if __name__ == "__main__":
    # First, ensure data files are built if they don't exist.
    # This might require importing and running build_CountryInfo if not automatically handled.
    # For now, assume build_CountryInfo is run by CountryInfo constructor or separately.
    
    country_name_to_test = 'US' # Or any other country code like 'FR', 'JP'
    c = CountryInfo(country_name_to_test)
    if c.info(): # Check if country info was loaded successfully
        print(f"Country: {c.name()} {c.flag()}")
        print(f"Capital: {c.capital()}")
        print(f"Continent: {c.continent()}")
        print(f"Population: {c.population()}")
        print(f"Languages: {c.languages()}")
        print(f"Currency: {c.currency()}")
        print(f"Neighbours: {c.neighbours()}")
        print(f"Timezones: {c.timezones()}")
        print(f"Major Cities: {c.major_cities()}")
        print(f"Alternate Names: {c.alternatenames()}")
        print(f"States: {c.states()}")

        print("\n--- All country data ---")
        # Pretty print the full info dictionary
        print(json.dumps(c.info(), indent=4, ensure_ascii=False)) # ensure_ascii=False for flags
    else:
        print(f"Could not find information for {country_name_to_test}")

    # Example for another country
    country_name_to_test_2 = 'FR' 
    c_fr = CountryInfo(country_name_to_test_2)
    if c_fr.info():
        print(f"\nCountry: {c_fr.name()} {c_fr.flag()}")
        print(f"Major Cities: {c_fr.major_cities()}")
    else:
        print(f"Could not find information for {country_name_to_test_2}")
