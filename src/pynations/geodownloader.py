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
import concurrent.futures
from menu import Menu
from tqdm import tqdm
from pathlib import Path
import pkg_resources
import time # Added for timing

DESTINATION = Path(pkg_resources.resource_filename('pynations','data/geonamesdata'))

class GeonamesDownloader:
    MAX_WORKERS = 5

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

    def _download_file_worker(self, url, filepath, error_message_template):
        try:
            r = requests.get(url, stream=True)
            # Ensure the destination directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            if r.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=self.CHUNKSIZE):
                        if chunk:
                            f.write(chunk)
                return f"Successfully downloaded {filepath.name}"
            else:
                return f"{error_message_template} (Status: {r.status_code}, URL: {url})"
        except Exception as e:
            return f"Error downloading {url}: {e}"

    def download_countries(self,optionType=None):
        """
        Downloads data for individual countries using parallel downloads.
        """
        self.countries = input("Enter Country code(s) <US,GB ..>: ").upper().split(',')
        
        tasks = []
        for country_code_raw in self.countries:
            country_code = country_code_raw.strip()
            if not country_code: continue # Skip empty country codes

            if optionType == 'G':
                url = GEONAMES + country_code + '.zip'
                fname = f'geonames_{country_code}.zip'
                err_template = f'Geonames information for {country_code} not found'
            elif optionType == 'A': # As per example, handle 'A' though not in original menu for this method
                url = ALTNAMES + country_code + '.zip'
                fname = f'altnames_{country_code}.zip'
                err_template = f'Alternate name information for {country_code} not found'
            else: # Default to 'Z' for zipcodes
                url = ZIPCODES + country_code + '.zip'
                fname = f'zipcodes_{country_code}.zip'
                err_template = f'Zipcode information for {country_code} not found'
            
            tasks.append({'url': url, 'filepath': DESTINATION.joinpath(fname), 'error_template': err_template})

        if not tasks:
            print("No valid country codes entered.")
            return

        print(f"Starting parallel download for {len(tasks)} country files...")
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            future_to_task = {
                executor.submit(self._download_file_worker, task['url'], task['filepath'], task['error_template']): task 
                for task in tasks
            }
            for future in tqdm(concurrent.futures.as_completed(future_to_task), total=len(tasks), desc="Downloading countries"):
                results.append(future.result())
        
        for res_msg in results:
            print(res_msg)

        # Update menu message
        country_list_str = ", ".join(self.countries)
        if optionType == 'G':
            self.geonames_menu.set_message(f'>> Geonames download for {country_list_str} completed <<\n\nPlease select an option')
        elif optionType == 'A':
            # Assuming there's an altnames_menu or handle appropriately
            # For now, let's print to console if menu object is not defined for 'A' in this context
            print(f'>> Altnames download for {country_list_str} completed <<')
            # self.altnames_menu.set_message(f'>> Altnames download for {country_list_str} completed <<\n\nPlease select an option')
        else: # 'Z'
            self.zipcodes_menu.set_message(f'>> Zipcode download for {country_list_str} completed <<\n\nPlease select an option')

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
    start_time = time.time()
    GeonamesDownloader().run()
    end_time = time.time()
    print(f"Total execution time for geodownloader: {end_time - start_time:.2f} seconds")
