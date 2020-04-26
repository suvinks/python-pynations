"""
Author  : Suvin Kannappil Sethumadhavan
Date    : April 19, 2020

Purpose : Download the databases from geonames.org website

Note: For country code options, give ISO2 country codes separated by commas
Example >> IN,US,GB
"""
GEONAMES = "http://download.geonames.org/export/dump/"
ZIPCODES = "http://download.geonames.org/export/zip/"
ALTNAMES = "http://download.geonames.org/export/dump/alternatenames/"

import requests
from menu import Menu
from tqdm import tqdm
from pathlib import Path
import pkg_resources

DESTINATION = Path(pkg_resources.resource_filename('pynations','data/geonamesdata'))

class GeonamesDownloader:
    def __init__(self):
        self.countries = []
        self.CHUNKSIZE = 2048

        geonames_options = [
            ("Specify Country code(s)", self.download_countries,{'optionType':'G'}),
            ("Download All-In-One file", self.download_all,{'optionType':'G'}),
            ("Go back", Menu.CLOSE)
        ]
        zipcodes_options = [
            ("Specify Country code(s)", self.download_countries,{'optionType':'Z'}),
            ("Download All-In-One file", self.download_all,{'optionType':'Z'}),
            ("Go back", Menu.CLOSE)
        ]

        self.geonames_menu = Menu(
            options=geonames_options,
            title="Downloading Geonames",
            message='Please select an option',
            auto_clear=False
        )
        self.geonames_menu.set_prompt('>>')


        self.zipcodes_menu = Menu(
            options=zipcodes_options,
            title="Downloading Zipcodes",
            message='Please select an option',
            auto_clear=False
        )
        self.zipcodes_menu.set_prompt('>>')


        self.main_options = [
            ("Download geonames", self.geonames_menu.open),
            ("Download zipcode data", self.zipcodes_menu.open),
            ("Download altnames data", self.download_all,{'optionType':'A'}),
            ("Download country info", self.download_all_countryinfo),
            ("Download supporting info",self.download_supporting_info),
            ("Exit", Menu.CLOSE)
        ]

        self.main_menu = Menu(
            title="Geonames.org data downloader",
            message="Please select an option",
            refresh=self.mainMenu)
        self.main_menu.set_prompt(">")


    def mainMenu(self):
        self.main_menu.set_options(self.main_options)

    def download_countries(self,optionType=None):
        """
        Downloads data for individual countries.
        Especially useful when you don't need the whole data

        Output Files
        ------------
        geonames_<countrycode>.zip
        altnames_<countrycode>.zip
        zipcodes_<countrycode>.zip
        """

        self.countries = input("Enter Country code(s) <US,GB ..>: ").upper().split(',')
        fname = ''
        err = ''

        for country in tqdm(self.countries):
            country = country.strip()

            if optionType == 'G':
                url = GEONAMES + country + '.zip'
                fname = 'geonames_'+country+'.zip'
                err = f'Geonames information for {country} not found'
            elif optionType == 'A':
                url = ALTNAMES + country + '.zip'
                fname = 'altnames_'+country+'.zip'
                err = f'Alternate name information for {country} not found'
            else:
                url = ZIPCODES + country + '.zip'
                fname = 'zipcodes_'+country+'.zip'
                err = f'Zipcode information for {country} not found'

            r = requests.get(url,stream=True)

            if r.status_code == 200:
                with open(str(DESTINATION.joinpath(fname)),'wb') as f:
                    for chunk in r.iter_content(chunk_size=self.CHUNKSIZE):
                        if chunk:
                            f.write(chunk)
            else:
                print(err)

        if optionType == 'G':
            self.geonames_menu.set_message(f'>> Geonames download for {self.countries} completed <<\n\nPlease select an option')
        elif optionType == 'A':
            self.altnames_menu.set_message(f'>> Altnames download for {self.countries} completed <<\n\nPlease select an option')
        else:
            self.zipcodes_menu.set_message(f'>> Zipcode download for {self.countries} completed <<\n\nPlease select an option')


    def download_all(self,optionType=None):
        """
        Downloads details of all countries.
        The downloads take a lot of time. Be absolutely sure before you go for this option.

        Output Files
        ------------
        geonames_allCountries.zip
        altnames_allCountries.zip
        zipcodes_allCountries.zip

        """
        if optionType == 'G':
            url = GEONAMES + "allCountries.zip"
            fname = "geonames_allCountries.zip"
            self.geonames_menu.set_message(f'>> Geonames download for all countries completed <<\n\nPlease select an option')
        elif optionType == 'A':
            url = GEONAMES + "alternateNamesV2.zip"
            fname = "alternateNamesV2.zip"
            self.main_menu.set_message(f'>> Altnames download for all countries completed <<\n\nPlease select an option')
        else:
            url = ZIPCODES + "allCountries.zip"
            fname = "zipcodes_allCountries.zip"
            self.zipcodes_menu.set_message(f'>> Zipcode download for all countries completed <<\n\nPlease select an option')

        print(f'Downloading data from {url} and saving to {fname}')

        r = requests.get(url,stream=True)
        if r.status_code == 200:
            with open(str(DESTINATION.joinpath(fname)),'wb') as f:
                for chunk in tqdm(r.iter_content(chunk_size=self.CHUNKSIZE)):
                    if chunk:
                        f.write(chunk)

    def download_all_countryinfo(self):
        """
        Downloading CountryInfo. This is a plain text file containing all the country details.
        """
        url = "http://download.geonames.org/export/dump/countryInfo.txt"
        print(f'Downloading {url} ...')
        r = requests.get(url)
        if r.status_code == 200:
            with open(str(DESTINATION.joinpath('countryInfo.txt')),'w') as f:
                f.write(r.content.decode('utf-8'))
        self.main_menu.set_message('>> Download completed for country info. <<\n\nPlease select an option')

    def download_supporting_info(self):
        """
        Downloading multiple support files. These are necessary for building
        country information
            1. Timezones
            2. admin1 codes
            3. admin2 codes
        """

        urls = ["http://download.geonames.org/export/dump/timeZones.txt",
                "http://download.geonames.org/export/dump/iso-languagecodes.txt",
                "http://download.geonames.org/export/dump/admin1CodesASCII.txt",
                "http://download.geonames.org/export/dump/admin2Codes.txt"]
        for url in urls:
            print(f'Downloading {url} ...')
            fname = url[url.rfind('/')+1:]
            r = requests.get(url)
            if r.status_code == 200:
                with open(str(DESTINATION.joinpath(fname)),'w') as f:
                    f.write(r.content.decode('utf-8'))
        self.main_menu.set_message('>> Download completed for supporting info. <<\n\nPlease select an option')

    def run(self):
        self.main_menu.open()

def download():
    GeonamesDownloader().run()

if __name__ == "__main__":
    GeonamesDownloader().run()
