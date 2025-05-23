from pathlib import Path
import sqlite3
from tqdm import tqdm
from unidecode import unidecode
import json
import os
import pkg_resources


DBFILE = Path(pkg_resources.resource_filename('pynations',
                                                'data/pynations.sqlite'))
COUNTRYINFOFILE = Path(pkg_resources.resource_filename('pynations',
                                                    'data/countryinfo.json'))
COUNTRYLOOKUPFILE = Path(pkg_resources.resource_filename('pynations',
                                                    'data/countrylookup.json'))

# Module-level caches
_cached_country_lookup = None
_cached_country_info = None

try:
    COLS = os.get_terminal_size()[0]
except:
    COLS = 80

CONTINENTS = {"AF":"Africa","AS":"Asia","EU":"Europe",
                "NA":"North America","OC":"Oceania","SA":"South America",
                "AN":"Antartica"}

Country = {   "Geonameid": 0,
              "ISO2": "",
              "ISO3": "",
              "ISO_Numeric": 0,
              "Fips": "",
              "Country": "",
              "AlternateNames": [],
              "Capital": "",
              "States": [],
              "Area": 0,
              "Population": "",
              "Continent": "",
              "Tld": "",
              "CurrencyCode": "",
              "CurrencyName": "",
              "Phone": "",
              "ZipCodeFormat": "",
              "ZipCodeRegex": "",
              "Languages": [],
              "Neighbours": [],
              "EquivalentFipsCode": "",
              "Timezones": [],
              "MajorCities": [],
              "Flag": ""
        }

def build_CountryInfo():

    '''
    Builds CountryInfo and CountryLookup files
    These files are necessary for CountryInfo to work
    '''

    #Check if CountryInfo and CountryLookup files exist
    if COUNTRYINFOFILE.exists() and COUNTRYLOOKUPFILE.exists():
        return True # No need to create the files

    ISO2_TO_FLAG = {
        "US": "🇺🇸",
        "CA": "🇨🇦",
        "GB": "🇬🇧",
        "FR": "🇫🇷",
        "DE": "🇩🇪",
        "JP": "🇯🇵",
        "IN": "🇮🇳",
        "BR": "🇧🇷",
        "AU": "🇦🇺",
        "CN": "🇨🇳"
    }

    if not DBFILE.exists():
        print('''Please import geodownloader and run download()
                and import geosqlite and run setupdb() before executing this''')
        exit(1)

    conn = sqlite3.connect(DBFILE)
    c = conn.cursor()
    c2 = conn.cursor()

    countrylookup = {}
    countries = {}

    print('='*COLS)
    print('Building Country Info and Country Lookup files'.center(COLS))
    print('='*COLS)

    c.execute('Select * from countryinfo;')
    c_result = c.fetchall()

    # Pre-fetch language mappings
    language_map = {}
    try:
        c2.execute("SELECT ISO639_1, ISO639_2, ISO639_3, language FROM languages")
        for iso1, iso2, iso3, lang_name in c2.fetchall():
            if iso1: language_map[iso1] = lang_name
            if iso2: language_map[iso2] = lang_name
            if iso3: language_map[iso3] = lang_name
    except sqlite3.Error as e:
        print(f"Error fetching language map: {e}. Language processing may be incomplete.")


    for row in tqdm(c_result):
        country = Country.copy()
        country['MajorCities'] = []
        country['Flag'] = ""

        (country["ISO2"],country["ISO3"],
        country["ISO_Numeric"],country["Fips"],
        country["Country"],country["Capital"],
        country["Area"],country["Population"],
        country["Continent"],country["Tld"],
        country["CurrencyCode"],country["CurrencyName"],
        country["Phone"],country["ZipCodeFormat"],
        country["ZipCodeRegex"],country["Languages"],country["Geonameid"],
        country["Neighbours"],country["EquivalentFipsCode"]) = row

        # Populate Flag
        if country["ISO2"] in ISO2_TO_FLAG:
            country["Flag"] = ISO2_TO_FLAG[country["ISO2"]]

        # Fetch Major Cities
        try:
            c2.execute("""
                SELECT name 
                FROM geoname 
                WHERE feature_class = 'P' 
                AND country_code = ? 
                ORDER BY population DESC 
                LIMIT 5
            """, (country["ISO2"],))
            country["MajorCities"] = [city_row[0] for city_row in c2.fetchall()]
        except sqlite3.Error as e:
            print(f"Error fetching major cities for {country['Country']} ({country['ISO2']}): {e}")
            country["MajorCities"] = []


        neighbours = country['Neighbours'].split(',')
        country['Neighbours'] = []
        if neighbours != ['']: # check if neighbours is not an empty string array
            c2.execute("Select name from countryinfo where ISO2 in (%s)" % ','.join('?' for i in neighbours),neighbours)
            country['Neighbours'] = [row[0] for row in c2.fetchall()]

        # country["Languages"] initially holds the raw language string from the database (e.g., "en,fr-CA")
        raw_langs_str = country["Languages"] 
        country["Languages"] = [] # Reset to store processed list of language names

        if raw_langs_str: # Ensure raw_langs_str is not empty or None
            langs_from_db = raw_langs_str.split(',')
            for lang_code_with_country in langs_from_db:
                if not lang_code_with_country: continue # Skip empty strings if "en,,fr"

                lang_code_base = lang_code_with_country
                country_suffix = ''
                if '-' in lang_code_with_country:
                    parts = lang_code_with_country.split('-', 1)
                    lang_code_base = parts[0]
                    if len(parts) > 1:
                        country_suffix = parts[1]
                
                language_name = language_map.get(lang_code_base)
                
                if language_name:
                    if country_suffix > '':
                        country["Languages"].append(f'{language_name} ({country_suffix})')
                    else:
                        country["Languages"].append(language_name)
                else:
                    # Optionally, handle cases where a language code from countryinfo isn't in the languages table
                    print(f"Warning: Language code '{lang_code_base}' not found in language map for country {country['Country']}. Original: '{lang_code_with_country}'")
                    # Fallback: append the original code or a placeholder
                    country["Languages"].append(lang_code_with_country) # Appending original as a fallback

        country["Continent"] = CONTINENTS[country["Continent"]]


        countrylookup[country['ISO2'].lower()] = country['Geonameid']
        countrylookup[country['ISO3'].lower()] = country['Geonameid']
        countrylookup[country['Country'].lower()] = country['Geonameid']
        countrylookup[unidecode(country['Country']).lower()] = country['Geonameid']

        # Fetching Alternate Names for the countries
        c2.execute("""Select distinct alternate_name from
                        countryaltnames where isolanguage not in ('link','wkdt') AND
                        geonameid=:geoid;""",{'geoid':country['Geonameid']})

        altnames = c2.fetchall()
        country['AlternateNames'] = [row[0] for row in altnames]

        for altname in altnames:
            countrylookup[altname[0].lower()] = country['Geonameid']
            countrylookup[unidecode(altname[0]).lower()] = country['Geonameid']

        c2.execute(f"""select name from admincodes WHERE
                            code like :countrycode||'.%' and
                            code not like :countrycode||'.%.%';""",
                            {'countrycode':country['ISO2']})

        country['States'] = [row[0] for row in c2.fetchall()]

        c2.execute("""select distinct
                            CASE when gmt_offset < '0.0' then 'GMT'||GMT_offset
                                 when gmt_offset > '0.0'  then 'GMT+'||GMT_offset
                                 when gmt_offset = '0.0'  then 'GMT'
                            End Timezone
                      from timezones where country = :cc;""",{'cc':country['ISO2']})
        country['Timezones'] = [row[0] for row in c2.fetchall()]
        #print(country['ISO2'],country['Timezones'])
        countries[country['Geonameid']] = country

    #Saving the information

    with open(COUNTRYINFOFILE,'w') as json_file:
        json.dump(countries,json_file)

    with open(COUNTRYLOOKUPFILE,'w') as json_file:
        json.dump(countrylookup,json_file)

    # Update caches after successful build
    global _cached_country_lookup, _cached_country_info
    _cached_country_lookup = countrylookup
    _cached_country_info = countries

    print(' Build Complete '.center(COLS,"#"))

    return True
    #pprint(countries)


class CountryInfo:
    '''
    Country Info class is used to represent the information of a given country.
    Any valid name for a country can be provided. There is no restrictions
    as to what language either as all unicode alternate names are supported.

    Usage
    -----
    c = CountryInfo('uk')   <-- This will load United Kingdom data
    c.info()                <-- Returns all the country information
    c.name()                <-- Returns countty name
    c.states()              <-- Returns states/provinces in the country
    c.currency()            <-- Returns currency code and name
    c.languages()           <-- Returns languages spoken
    c.neighbours()          <-- Returns neighbouring country names
    c.capital()             <-- Returns the Capital
    c.timezones()           <-- Returns the list of timezones
    c.population()          <-- Returns the population
    c.continent()           <-- Returns the continent

    allcountries = CountryInfo().all()

    The above function would return all the countries in a dictionary form
    with geonameid from geonames.org as the key
    '''
    country = None
    # Instance variable self.countrylookup is no longer used. Global _cached_country_lookup is used directly.

    def __init__(self,countryname=None):
        global _cached_country_lookup, _cached_country_info
        
        build_CountryInfo() # Ensures files are created if they don't exist and populates caches if it builds.
                            # If files exist, it returns True quickly; caches might still be None if first run.

        if _cached_country_lookup is None:
            # build_CountryInfo returned (files exist) or failed, but cache is not populated. Load from file.
            if COUNTRYLOOKUPFILE.exists():
                with open(COUNTRYLOOKUPFILE, 'r') as f:
                    _cached_country_lookup = json.load(f)
            else:
                # This implies build_CountryInfo() failed to create the file or it was deleted.
                print(f"Warning: {COUNTRYLOOKUPFILE} not found. Lookup will be empty.")
                _cached_country_lookup = {} # Initialize to empty to prevent errors on access.
        
        if countryname:
            countryname_lower = countryname.lower()
            # Ensure _cached_country_lookup is not None before trying to access it
            if _cached_country_lookup and countryname_lower in _cached_country_lookup:
                geoid = _cached_country_lookup[countryname_lower]

                if _cached_country_info is None:
                    # Cache not populated, load from file.
                    if COUNTRYINFOFILE.exists():
                        with open(COUNTRYINFOFILE, 'r') as f:
                            _cached_country_info = json.load(f)
                    else:
                        print(f"Warning: {COUNTRYINFOFILE} not found. Country info will be empty.")
                        _cached_country_info = {} # Initialize to empty.
                
                # Ensure _cached_country_info is not None before .get()
                if _cached_country_info:
                    self.country = _cached_country_info.get(str(geoid))
                    if self.country is None:
                        print(f'Country information not found for geoid {geoid} (derived from {countryname}) in cached/loaded data.')
                else: # _cached_country_info is still None or empty after attempting to load
                     self.country = None
                     print(f'Country info data is not available for geoid {geoid}.')
            else:
                print(f'Country {countryname} not found in lookup data.')
        # If countryname is None, self.country remains None as per class attribute default.

    def info(self):
        return self.country if self.country else None

    def name(self):
        return self.country['Country'] if self.country else None

    def states(self):
        return self.country['States'] if self.country else None

    def currency(self):
        return (self.country['CurrencyCode'],self.country['CurrencyName']) if self.country else None

    def capital(self):
        return self.country['Capital'] if self.country else None

    def continent(self):
        return self.country['Continent'] if self.country else None

    def neighbours(self):
        return self.country['Neighbours'] if self.country else None

    def neighbors(self):
        return self.country['Neighbours'] if self.country else None

    def population(self):
        return self.country['Population'] if self.country else None

    def alternatenames(self):
        return self.country['AlternateNames'] if self.country else None

    def timezones(self):
        return self.country['Timezones'] if self.country else None

    def languages(self):
        return self.country['Languages'] if self.country else None

    def major_cities(self):
        return self.country['MajorCities'] if self.country and 'MajorCities' in self.country else []

    def flag(self):
        return self.country['Flag'] if self.country and 'Flag' in self.country else ""

    def all(self):
        global _cached_country_info
        
        build_CountryInfo() # Ensure data files are potentially built/updated.

        if _cached_country_info is None:
            # Cache not populated (e.g. first call, or build_CountryInfo returned early due to existing files).
            if COUNTRYINFOFILE.exists():
                with open(COUNTRYINFOFILE, 'r') as f:
                    _cached_country_info = json.load(f)
            else:
                # This implies build_CountryInfo() failed or files were deleted.
                print(f"Warning: {COUNTRYINFOFILE} not found. Returning empty data for all().")
                _cached_country_info = {} # Default to empty dict.
        return _cached_country_info


if __name__ == "__main__":
    # Existing demonstration code
    print("Basic CountryInfo Demonstration:")
    c = CountryInfo('us')
    if c.info():
        print(f"Name: {c.name()}")
        print(f"States: {c.states()}")
        print(f"Currency: {c.currency()}")
        print(f"Neighbours: {c.neighbours()}")
        print(f"Continent: {c.continent()}")
        print(f"Flag: {c.flag()}")
        print(f"Major Cities: {c.major_cities()}")
    else:
        print("US info not found for basic demonstration.")

    # New benchmark demonstration
    import time

    print("\n" + "="*30)
    print("Benchmarking CountryInfo Access")
    print("="*30)

    # Time the first access (might include reading files if cache is cold)
    start_time = time.time()
    c_us_first = CountryInfo('US')
    if c_us_first.info():
        print(f"First access for US ({c_us_first.name()} {c_us_first.flag()}) took: {time.time() - start_time:.6f} seconds")
    else:
        print("US info not found for first access benchmark.")

    # Time a subsequent access (should be faster due to cache)
    start_time = time.time()
    c_us_second = CountryInfo('US')
    if c_us_second.info():
        print(f"Second access for US ({c_us_second.name()}) took: {time.time() - start_time:.6f} seconds")
    else:
        print("US info not found for second access benchmark.")

    # Time another country (first access for this country, but lookup cache might be warm)
    start_time = time.time()
    c_fr = CountryInfo('FR')
    if c_fr.info():
        print(f"First access for FR ({c_fr.name()} {c_fr.flag()}) took: {time.time() - start_time:.6f} seconds")
    else:
        print("FR info not found for benchmark.")
    
    # Time CountryInfo().all() - first call
    start_time = time.time()
    all_countries_first = CountryInfo().all()
    count_first = len(all_countries_first) if all_countries_first else 0 # Handle if all_countries_first is None
    print(f"First call to CountryInfo().all() (loaded {count_first} countries) took: {time.time() - start_time:.6f} seconds")

    # Time CountryInfo().all() - second call (should be cached)
    start_time = time.time()
    all_countries_second = CountryInfo().all()
    count_second = len(all_countries_second) if all_countries_second else 0 # Handle if all_countries_second is None
    print(f"Second call to CountryInfo().all() (loaded {count_second} countries) took: {time.time() - start_time:.6f} seconds")

    # Advise user that build_CountryInfo() can take time if data files are not present
    print("\nNote: If data files (countryinfo.json, countrylookup.json) were built during this run,")
    print("the very first CountryInfo() call would include that one-time build duration.")
    print("Run this script again when files already exist to see typical access times.")
