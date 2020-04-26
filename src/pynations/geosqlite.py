"""
Author  : Suvin Kannappil Sethumadhavan
Date    : April 20, 2020

Purpose : Load the geonames data to SQLite tables
"""

from tqdm import tqdm
from pathlib import Path
import sqlite3
import os
from zipfile import ZipFile
import pkg_resources

SOURCE = Path(pkg_resources.resource_filename('pynations','data/geonamesdata'))
DBFILE = Path(pkg_resources.resource_filename('pynations','data/pynations.sqlite'))

try:
    COLS = os.get_terminal_size()[0]
except:
    COLS = 80

def findFiles(directory='.',exts=None,recursive=True,returnString=True):
    '''
        Find files inside a given directory. The file types can be given as a string or list.
        The files can be searched recursively inside subfolders too

        Returns the files as a list. Returns empty list if no files are found with respect to given condition.

        Ignores files/directory names starting with '.' which happens in Windows
    '''
    files = []
    path = Path(directory)

    if exts and isinstance(exts,str):
        exts = [exts]

    if recursive:
        files = [p for p in path.rglob('*.*') if (((exts is None) or (p.suffix.lower() in exts)) and not p.name.startswith('.'))]
    else:
        files = [p for p in path.iterdir() if (((exts is None) or (p.suffix.lower() in exts)) and not p.name.startswith('.'))]

    if not returnString:
        return files
    else:
        return [str(p) for p in files]

# Connecting to the SQLite db File. If it doesn't exist then the command
# will create it
dbexists = DBFILE.exists()
conn = sqlite3.connect(str(DBFILE))
c = conn.cursor()

if not dbexists:    # Now we need to create the tables
    print('-'*COLS)
    print("BUILDING PYNATION TABLES".center(COLS))
    print('-'*COLS)

    with conn:
        c.execute("""create table geonames   (geonameid INTEGER PRIMARY KEY,
                                              name TEXT,
                                              asciiname TEXT,
                                              alternatenames TEXT,
                                              latitude DECIMAL(10,7),
                                              longitude DECIMAL(10,7),
                                              feature_class TEXT,
                                              feature_code TEXT,
                                              country TEXT,
                                              cc2 TEXT,
                                              admin1 TEXT,
                                              admin2 TEXT,
                                              admin3 TEXT,
                                              admin4 TEXT,
                                              population INTEGER,
                                              elevation INTEGER,
                                              dem INTEGER,
                                              timezone TEXT,
                                              modification_date DATETIME);""")

        c.execute("create index onname on geonames(name);")
        c.execute("create index onasciiname on geonames(asciiname);")
        c.execute("create index onaltnames on geonames(alternatenames);")
        print(" GEONAMES - TABLE BUILD COMPLETE ".center(COLS,'-'))

        c.execute("""create table zipcodes (country TEXT,
                                            zipcode TEXT,
                                            place_name TEXT,
                                            state_name TEXT,
                                            state_code TEXT,
                                            county_name TEXT,
                                            county_code TEXT,
                                            community_name TEXT,
                                            community_code TEXT,
                                            latitude DECIMAL(10,7),
                                            longitude DECIMAL(10,7),
                                            accuracy INTEGER);""")

        c.execute("create index zipcode on zipcodes(zipcode);")
        c.execute("create index zipcountry on zipcodes(country);")
        c.execute("create index zipnames on zipcodes(place_name);")
        print(" ZIPCODES - TABLE BUILD COMPLETE ".center(COLS,'-'))

        c.execute("""create table altnames (alternateNameId INTEGER PRIMARY KEY,
                                            geonameId INTEGER,
                                            isolanguage TEXT,
                                            alternate_name TEXT,
                                            isPreferredName INTEGER,
                                            isShortName INTEGER,
                                            isColloquial INTEGER,
                                            isHistoric INTEGER,
                                            from_date TEXT,
                                            to_date TEXT);""")

        c.execute("create index altnames_idx on altnames(alternate_name);")
        c.execute("create index altnames_idx2 on altnames(geonameId);")

        print(" ALTNAMES - TABLE BUILD COMPLETE ".center(COLS,'-'))

        c.execute("""create table countryinfo  (iso2 TEXT PRIMARY KEY,
                                                iso3 TEXT,
                                                iso_numeric INTEGER,
                                                fips_code TEXT,
                                                name TEXT,
                                                capital TEXT,
                                                area REAL,
                                                population INTEGER,
                                                continent TEXT,
                                                tld TEXT,
                                                currency TEXT,
                                                currencyName TEXT,
                                                phone TEXT,
                                                zipcode_format TEXT,
                                                zipcode_regex TEXT,
                                                languages TEXT,
                                                geonameId INTEGER,
                                                neighbours TEXT,
                                                equivalent_fipscode TEXT);""")

        c.execute("create index iso_3 on countryinfo(iso3);")
        print(" COUNTRYINFO - TABLE BUILD COMPLETE ".center(COLS,'-'))

        c.execute("""create table countryaltnames (alternateNameId INTEGER PRIMARY KEY,
                                                    geonameId INTEGER,
                                                    isolanguage TEXT,
                                                    alternate_name TEXT,
                                                    isPreferredName INTEGER,
                                                    isShortName INTEGER,
                                                    isColloquial INTEGER,
                                                    isHistoric INTEGER,
                                                    from_date TEXT,
                                                    to_date TEXT);""")

        c.execute("create index caltnames_idx on countryaltnames(alternate_name);")
        c.execute("create index caltnames_idx2 on countryaltnames(geonameId);")
        print(" COUNTRYALTNAMES - TABLE BUILD COMPLETE ".center(COLS,'-'))

        c.execute("""create table admincodes   (code TEXT PRIMARY KEY,
                                                name TEXT,
                                                asciiname TEXT,
                                                geonameId INTEGER);""")

        c.execute("create index admincode_idx1 on admincodes(geonameId);")
        c.execute("create index admincode_idx2 on admincodes(name);")
        print(" ADMINCODES - TABLE BUILD COMPLETE ".center(COLS,'-'))

        c.execute("""create table timezones   (country TEXT,
                                                timezoneid TEXT,
                                                GMT_offset TEXT,
                                                DST_offset TEXT,
                                                RAW_offset TEXT);""")

        c.execute("create index timezones_idx1 on timezones(country);")
        print(" TIMEZONES - TABLE BUILD COMPLETE ".center(COLS,'-'))

        c.execute("""create table languages   (ISO639_3 TEXT,
                                                ISO639_2 TEXT,
                                                ISO639_1 TEXT,
                                                language TEXT);""")

        c.execute("create index languages_idx1 on languages(ISO639_2);")
        print(" LANGUAGES - TABLE BUILD COMPLETE ".center(COLS,'-'))

        print(' PYNATION TABLE BUILD COMPLETE '.center(COLS,'#'))

# Check and import the data
files = findFiles(SOURCE,recursive=False)

if files == []:
    print('No files to import')
    exit(1)

def load_countryinfo():
    countryinfopath = str(SOURCE.joinpath("countryInfo.txt"))
    if  countryinfopath in files:
        print('='*COLS)
        print("Loading countryInfo file to db")
        print('='*COLS)
        print("Removing existing entries ...")
        with conn:
            c.execute(f'DELETE FROM countryinfo;')
        print("Importing data ...")
        cmd = f"""sed $'/^#/d' {countryinfopath} > {str(SOURCE.joinpath("temp.txt"))} """
        rc = os.system(cmd)

        cmd = f""" sqlite3 {DBFILE} <<< ".mode tabs\n.import {str(SOURCE.joinpath("temp.txt"))} countryinfo" """
        rc = os.system(cmd)
        if rc == 0:
            print(f'Data import successful for countryinfo')
        else:
            print(f'Data import failed with {rc} for countryinfo')
        print('#'*COLS)

def load_geodata(recordtype):
    #Find if there are any geoname Files
    geofiles = [file for file in files if file.find(f'{recordtype}_') > -1 and
                                            file.endswith('.zip')]

    if geofiles != []:
        print('='*COLS)
        print(f"Processing {recordtype.upper()} files")
        print('='*COLS)

        for file in tqdm(geofiles):
            # Unzip the file and extract the text files
            idx = file.find(f'{recordtype}_')
            countrycode = file[idx:].replace(f'{recordtype}_','').replace('.zip','')
            infile = f'{countrycode}.txt'
            outfile = f'{recordtype}_'+infile

            with ZipFile(file, 'r') as zipObj:
                # Get a list of all archived file names from the zip
                print(f'Unzipping {infile} ...')
                zipObj.extract(infile,str(SOURCE))
                os.rename(str(SOURCE.joinpath(infile)),
                            str(SOURCE.joinpath(outfile)))

            print("Removing existing entries ...")
            with conn:
                if recordtype != 'altnames':
                    c.execute(f'DELETE FROM {recordtype} WHERE country = :value;',{'value':countrycode})
                else:
                    c.execute(f'DELETE FROM {recordtype} WHERE geonameId IN (SELECT geonameId from geonames WHERE country = :value);',{'value':countrycode})

            print("Importing data ...")
            cmd = f"""sed $'s/"/""/g;s/[^\t]*/"&"/g' {str(SOURCE.joinpath(outfile))} > {str(SOURCE.joinpath('quoted.txt'))} """
            #print(SOURCE.joinpath(outfile).resolve())
            rc = os.system(cmd)

            cmd = f""" sqlite3 {DBFILE} <<< ".mode tabs\n.separator \\t\n.import {str(SOURCE.joinpath('quoted.txt'))} {recordtype}" """
            #print(cmd)
            #rc=0
            rc = os.system(cmd)
            if rc == 0:
                print(f'Data import successful for {infile}')
                os.remove(str(SOURCE.joinpath(outfile)))
            else:
                print(f'Data import failed with {rc} for {infile}')
        print('#'*COLS)


def load_all_geodata(filename):

    file = str(SOURCE.joinpath(filename))
    infile = str(Path(filename).with_suffix('.txt'))
    recordtype = ''

    # if the filename ends with zip, extract the files
    if file.lower().endswith('.zip'):
        with ZipFile(file, 'r') as zipObj:
            # Get a list of all archived file names from the zip
            print(f'Unzipping {file} ...')
            zipObj.extract(infile,str(SOURCE))

    print("Removing existing entries ...")
    with conn:
        if filename.lower().startswith('alternatenamesv2'):
            recordtype = 'altnames'
            c.execute(f'DELETE FROM altnames;')

    if recordtype == '':
        exit()

    print("Importing data ...")
    cmd = f"""sed $'s/"/""/g;s/[^\t]*/"&"/g' {str(SOURCE.joinpath(infile))} > {str(SOURCE.joinpath('quoted.txt'))} """
    rc = os.system(cmd)

    cmd = f""" sqlite3 {DBFILE} <<< ".mode tabs\n.separator \\t\n.import {str(SOURCE.joinpath('quoted.txt'))} {recordtype}" """
    rc = os.system(cmd)
    if rc == 0:
        print(f'Data import successful for {infile}')
        os.remove(str(SOURCE.joinpath(infile)))

        print(f'Populating countryaltnames table')
        #Populate country altnames
        caltnamequery = "INSERT INTO countryaltnames SELECT * from altnames where geonameid in (select geonameid from countryinfo);"
        with conn:
            c.execute('DELETE FROM countryaltnames;')
            c.execute(caltnamequery)
    else:
        print(f'Data import failed with {rc} for {infile}')
    print('#'*COLS)

def load_admincodes():
    files = ['admin1CodesASCII.txt','admin2Codes.txt']

    fnames = []
    #Check if both files exists
    for file in files:
        fname = str(SOURCE.joinpath(file))
        if Path(fname).exists():
            fnames.append(fname)

    if fnames != []:
        #Remove existing records
        print("Deleting existing data ...")
        with conn:
            c.execute('DELETE FROM admincodes;')

        print("Importing data ...")
        for fname in fnames:
            cmd = f"""sed $'s/"/""/g;s/[^\t]*/"&"/g' {fname} > {str(SOURCE.joinpath('quoted.txt'))} """
            #print(SOURCE.joinpath(outfile).resolve())
            rc = os.system(cmd)

            cmd = f""" sqlite3 {DBFILE} <<< ".mode tabs\n.separator \\t\n.import {str(SOURCE.joinpath('quoted.txt'))} admincodes" """
            #print(cmd)
            #rc=0
            rc = os.system(cmd)
            if rc == 0:
                print(f'Data import successful for {fname}')
            else:
                print(f'Data import failed with {rc} for {fname}')
    print('#'*COLS)

def load_timezones():

    file = "timeZones.txt"

    if Path(SOURCE.joinpath(file)).exists():
        #Remove existing records
        fname = str(SOURCE.joinpath(file))
        print("Deleting existing data ...")
        with conn:
            c.execute('DELETE FROM timezones;')

        print("Importing data ...")
        cmd = f"""sed $'s/"/""/g;s/[^\t]*/"&"/g' {fname} > {str(SOURCE.joinpath('quoted.txt'))} """
        #print(SOURCE.joinpath(outfile).resolve())
        rc = os.system(cmd)

        cmd = f""" sqlite3 {DBFILE} <<< ".mode tabs\n.separator \\t\n.import {str(SOURCE.joinpath('quoted.txt'))} timezones" """
        #print(cmd)
        #rc=0
        rc = os.system(cmd)
        if rc == 0:
            print(f'Data import successful for {file}')
        else:
            print(f'Data import failed with {rc} for {file}')
    print('#'*COLS)

def load_languages():

    file = "iso-languagecodes.txt"

    if Path(SOURCE.joinpath(file)).exists():
        #Remove existing records
        fname = str(SOURCE.joinpath(file))
        print("Deleting existing data ...")
        with conn:
            c.execute('DELETE FROM languages;')

        print("Importing data ...")
        cmd = f"""sed $'s/"/""/g;s/[^\t]*/"&"/g' {fname} > {str(SOURCE.joinpath('quoted.txt'))} """
        #print(SOURCE.joinpath(outfile).resolve())
        rc = os.system(cmd)

        cmd = f""" sqlite3 {DBFILE} <<< ".mode tabs\n.separator \\t\n.import {str(SOURCE.joinpath('quoted.txt'))} languages" """
        #print(cmd)
        #rc=0
        rc = os.system(cmd)
        if rc == 0:
            print(f'Data import successful for {file}')
        else:
            print(f'Data import failed with {rc} for {file}')
    print('#'*COLS)

def setupdb():
    load_countryinfo()
    load_timezones()
    load_languages()
    load_admincodes()

    for recordtype in ['geonames','zipcodes']:
        load_geodata(recordtype)

    for filename in ['alternateNamesV2.zip']:
        load_all_geodata(filename)

def main():
    setupdb()

if __name__ == "__main__":
    main()
