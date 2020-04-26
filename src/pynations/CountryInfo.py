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
              "Timezones": []
        }

def build_CountryInfo():

    '''
    Builds CountryInfo and CountryLookup files
    These files are necessary for CountryInfo to work
    '''

    #Check if CountryInfo and CountryLookup files exist
    if COUNTRYINFOFILE.exists() and COUNTRYLOOKUPFILE.exists():
        return True # No need to create the files

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

    for row in tqdm(c_result):
        country = Country.copy()

        (country["ISO2"],country["ISO3"],
        country["ISO_Numeric"],country["Fips"],
        country["Country"],country["Capital"],
        country["Area"],country["Population"],
        country["Continent"],country["Tld"],
        country["CurrencyCode"],country["CurrencyName"],
        country["Phone"],country["ZipCodeFormat"],
        country["ZipCodeRegex"],country["Languages"],country["Geonameid"],
        country["Neighbours"],country["EquivalentFipsCode"]) = row

        neighbours = country['Neighbours'].split(',')
        country['Neighbours'] = []
        if neighbours != []:
            c2.execute("Select name from countryinfo where ISO2 in (%s)" % ','.join('?' for i in neighbours),neighbours)
            country['Neighbours'] = [row[0] for row in c2.fetchall()]

        langs = country["Languages"].split(',')

        country["Languages"] = []
        for lang in langs:
            lang = lang if lang.find('-') > 0 else lang+'-'
            lang,cntry = lang.split('-')
            #print(lang,cntry)
            c2.execute("""Select distinct language
                            from languages
                            where ISO639_1 = :lang
                                OR ISO639_2 = :lang
                                OR ISO639_3 = :lang;""",{'lang':lang})
            language = c2.fetchone()[0]
            if cntry > '':
                country["Languages"].append(f'{language} ({cntry})')
            else:
                country["Languages"].append(language)

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
    countrylookup = None

    def __init__(self,countryname=None):

        if build_CountryInfo():
            #Load the country Lookup File

            if countryname:
                self.countrylookup = json.load(open(COUNTRYLOOKUPFILE))
                if countryname.lower() in self.countrylookup:
                    geoid = self.countrylookup[countryname.lower()]

                    #Now load the country information
                    countryinfo = json.load(open(COUNTRYINFOFILE))
                    self.country = countryinfo[str(geoid)]
                else:
                    print(f'Country information not found for {countryname}')

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

    def all(self):
        return json.load(open(COUNTRYINFOFILE))


if __name__ == "__main__":
    c = CountryInfo('us')
    print(c.name())
    print(c.states())
    print(c.currency())
    print(c.neighbours())
    print(c.continent())
