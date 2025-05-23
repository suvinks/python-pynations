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
import csv # Added for CSV parsing
import io # Added for reading from zip stream
import time # Added for timing

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
    file = "countryInfo.txt"
    filepath = SOURCE.joinpath(file)
    BATCH_SIZE = 1000

    # The global 'files' list check might be inconsistent if findFiles isn't re-run or if file appears later.
    # Direct check with filepath.exists() is more reliable here.
    if not filepath.exists():
        print(f"File {file} not found at {filepath}")
        print('#'*COLS)
        return

    print('='*COLS)
    print(f"Processing {file} into countryinfo table")
    print('='*COLS)
    
    try:
        with conn: 
            c.execute('DELETE FROM countryinfo;')
        
        batch = []
        # Table: countryinfo (19 columns as per schema)
        sql = """INSERT INTO countryinfo (iso2, iso3, iso_numeric, fips_code, name, capital, area, 
                                        population, continent, tld, currency, currencyName, phone, 
                                        zipcode_format, zipcode_regex, languages, geonameId, 
                                        neighbours, equivalent_fipscode) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        
        processed_rows = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            
            for row_num, row in enumerate(reader, 1):
                if not row or (row and row[0].startswith('#')): # Skip empty rows or comments
                    continue
                
                if len(row) == 19:
                    try:
                        # Ensure values are correctly mapped to schema
                        # iso2, iso3, iso_numeric, fips_code, name, capital, area, population, continent, tld, 
                        # currency, currencyName, phone, zipcode_format, zipcode_regex, languages, geonameId, 
                        # neighbours, equivalent_fipscode
                        
                        iso2 = row[0]
                        iso3 = row[1]
                        iso_numeric = int(row[2]) if row[2] else None
                        fips_code = row[3]
                        name = row[4]
                        capital = row[5]
                        area = float(row[6]) if row[6] else None 
                        population = int(row[7]) if row[7] else None
                        continent = row[8]
                        tld = row[9]
                        currency = row[10] 
                        currencyName = row[11]
                        phone = row[12]
                        zipcode_format = row[13]
                        zipcode_regex = row[14]
                        languages = row[15] 
                        geonameId = int(row[16]) if row[16] else None
                        neighbours = row[17] 
                        equivalent_fipscode = row[18]

                        batch.append((iso2, iso3, iso_numeric, fips_code, name, capital, area,
                                      population, continent, tld, currency, currencyName, phone,
                                      zipcode_format, zipcode_regex, languages, geonameId,
                                      neighbours, equivalent_fipscode))
                        processed_rows += 1
                        
                        if len(batch) >= BATCH_SIZE:
                            c.executemany(sql, batch)
                            conn.commit() 
                            batch = []
                    except ValueError as ve:
                        print(f"Warning: Row {row_num}: Error converting value: {ve} - Row: {row}")
                    except IndexError: # Should not happen if len(row) == 19 check is effective
                        print(f"Warning: Row {row_num}: Malformed row (not enough columns): {row}")
                elif row: # Non-empty row, but not 19 columns and not a comment
                    print(f"Warning: Row {row_num}: Skipping malformed row (expected 19 columns, got {len(row)}): {row}")
            
            if batch: 
                c.executemany(sql, batch)
                conn.commit() 
        print(f"Successfully loaded {processed_rows} records from {file} into countryinfo table.")
    except sqlite3.Error as e:
        conn.rollback() 
        print(f"SQLite error during loading {file}: {e}")
    except Exception as e:
        conn.rollback() 
        print(f"General error processing file {file}: {e}")
    print('#'*COLS)

def load_geodata(recordtype):
    # files is a global list of file paths (strings)
    zip_files_to_process = [Path(f) for f in files if f.find(f'{recordtype}_') > -1 and f.endswith('.zip')]
    BATCH_SIZE = 1000

    if not zip_files_to_process:
        print(f"No .zip files found for record type '{recordtype}' in {SOURCE}")
        return

    print('='*COLS)
    print(f"Processing {recordtype.upper()} files")
    print('='*COLS)

    for zip_filepath_obj in tqdm(zip_files_to_process, desc=f"Processing {recordtype} zip files"):
        zip_filepath_str = str(zip_filepath_obj)
        try:
            # Derive countrycode and expected text file name within the zip
            # Example: geonames_US.zip -> countrycode='US', text_filename_in_zip='US.txt'
            # Example: zipcodes_FR.zip -> countrycode='FR', text_filename_in_zip='FR.txt'
            base_zip_name = zip_filepath_obj.name
            countrycode = base_zip_name.replace(f'{recordtype}_', '').replace('.zip', '')
            text_filename_in_zip = f"{countrycode}.txt"

            print(f"\nProcessing {zip_filepath_obj.name} for country {countrycode}...")

            # Delete existing records for this country
            with conn:
                delete_sql = f"DELETE FROM {recordtype} WHERE country = ?"
                c.execute(delete_sql, (countrycode,))
            print(f"Removed existing {recordtype} entries for country {countrycode}.")

            batch = []
            sql_insert = ""
            expected_cols = 0

            if recordtype == 'geonames':
                expected_cols = 19
                sql_insert = """INSERT INTO geonames (geonameid, name, asciiname, alternatenames, latitude, longitude, 
                                                  feature_class, feature_code, country, cc2, admin1, admin2, admin3, admin4, 
                                                  population, elevation, dem, timezone, modification_date) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
            elif recordtype == 'zipcodes':
                expected_cols = 12
                sql_insert = """INSERT INTO zipcodes (country, zipcode, place_name, state_name, state_code, 
                                                   county_name, county_code, community_name, community_code, 
                                                   latitude, longitude, accuracy) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"""
            else:
                print(f"Unsupported recordtype: {recordtype}. Skipping {zip_filepath_obj.name}.")
                continue
            
            processed_rows_in_file = 0
            with ZipFile(zip_filepath_str, 'r') as zf:
                if text_filename_in_zip not in zf.namelist():
                    print(f"Warning: Expected file '{text_filename_in_zip}' not found in '{zip_filepath_obj.name}'. Skipping.")
                    # Attempt to find any .txt file if the exact name isn't found (common for some geonames zips)
                    txt_files_in_zip = [name for name in zf.namelist() if name.lower().endswith('.txt') and not name.lower().startswith('readme')]
                    if len(txt_files_in_zip) == 1:
                        text_filename_in_zip = txt_files_in_zip[0]
                        print(f"Found alternative text file: '{text_filename_in_zip}'. Proceeding.")
                    else:
                        print(f"Could not identify a unique data file in '{zip_filepath_obj.name}'. Skipping.")
                        continue

                with zf.open(text_filename_in_zip, 'r') as member_file:
                    text_stream = io.TextIOWrapper(member_file, encoding='utf-8')
                    reader = csv.reader(text_stream, delimiter='\t', quoting=csv.QUOTE_NONE)
                    
                    for row_num, row in enumerate(reader, 1):
                        if not row or len(row) != expected_cols:
                            if row: # Only print warning if row is not completely empty
                                print(f"Warning: Row {row_num} in {text_filename_in_zip} from {zip_filepath_obj.name}: Skipping malformed row (expected {expected_cols}, got {len(row)}): {row}")
                            continue
                        
                        try:
                            if recordtype == 'geonames':
                                data_tuple = (
                                    int(row[0]) if row[0] else None, # geonameid
                                    row[1], row[2], row[3], # name, asciiname, alternatenames
                                    float(row[4]) if row[4] else None, # latitude
                                    float(row[5]) if row[5] else None, # longitude
                                    row[6], row[7], row[8], row[9], # feature_class, feature_code, country, cc2
                                    row[10], row[11], row[12], row[13], # admin1-4
                                    int(row[14]) if row[14] else None, # population
                                    int(row[15]) if row[15] else None, # elevation
                                    int(row[16]) if row[16] else None, # dem
                                    row[17], row[18] # timezone, modification_date
                                )
                            elif recordtype == 'zipcodes':
                                data_tuple = (
                                    row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], # text fields up to community_code
                                    float(row[9]) if row[9] else None,   # latitude
                                    float(row[10]) if row[10] else None, # longitude
                                    int(row[11]) if row[11] else None    # accuracy
                                )
                            
                            batch.append(data_tuple)
                            processed_rows_in_file += 1
                            if len(batch) >= BATCH_SIZE:
                                c.executemany(sql_insert, batch)
                                conn.commit()
                                batch = []
                        except ValueError as ve:
                            print(f"Warning: Row {row_num} in {text_filename_in_zip} from {zip_filepath_obj.name}: Error converting value: {ve} - Row: {row}")
            
            if batch:
                c.executemany(sql_insert, batch)
                conn.commit()
            print(f"Successfully loaded {processed_rows_in_file} records from {text_filename_in_zip} (in {zip_filepath_obj.name}).")

        except sqlite3.Error as e_sqlite:
            conn.rollback()
            print(f"SQLite error processing file {zip_filepath_obj.name}: {e_sqlite}. Rolled back changes for this file.")
        except Exception as e_file:
            print(f"General error processing file {zip_filepath_obj.name}: {e_file}")
            # conn.rollback() might be needed if error is after some commits for this file.
            # For simplicity, assuming commit happens per file or per batch.
    print('#'*COLS)

def load_all_geodata(zip_filename): # Parameter is typically 'alternateNamesV2.zip'
    BATCH_SIZE = 1000
    # Expected text file within the zip, e.g., 'alternateNamesV2.txt'
    text_filename_in_zip = Path(zip_filename).with_suffix('.txt').name 
    target_table = 'altnames' # This function is specifically for altnames

    zip_filepath = SOURCE.joinpath(zip_filename)

    if not zip_filepath.exists():
        print(f"Zip file {zip_filename} not found at {zip_filepath}. Skipping.")
        return

    print('='*COLS)
    print(f"Processing {zip_filename} into {target_table} table")
    print('='*COLS)

    try:
        # Delete existing records from the target table
        with conn:
            c.execute(f'DELETE FROM {target_table};')
        print(f"Removed existing entries from {target_table} table.")

        batch = []
        # altnames table: alternateNameId, geonameId, isolanguage, alternate_name, 
        #                 isPreferredName, isShortName, isColloquial, isHistoric, from_date, to_date (10 columns)
        sql_insert = """INSERT INTO altnames (alternateNameId, geonameId, isolanguage, alternate_name, 
                                            isPreferredName, isShortName, isColloquial, isHistoric, 
                                            from_date, to_date) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        
        processed_rows_in_file = 0
        with ZipFile(zip_filepath, 'r') as zf:
            if text_filename_in_zip not in zf.namelist():
                # Fallback: try to find any .txt file if expected name isn't there.
                alt_txt_files = [name for name in zf.namelist() if name.lower().endswith('.txt') and 'readme' not in name.lower()]
                if len(alt_txt_files) == 1:
                    text_filename_in_zip = alt_txt_files[0]
                    print(f"Warning: Expected file '{Path(zip_filename).with_suffix('.txt').name}' not found. Using '{text_filename_in_zip}' instead.")
                else:
                    print(f"Error: Expected file '{Path(zip_filename).with_suffix('.txt').name}' not found in '{zip_filename}' and could not determine a unique alternative. Found: {alt_txt_files}")
                    return

            with zf.open(text_filename_in_zip, 'r') as member_file:
                text_stream = io.TextIOWrapper(member_file, encoding='utf-8')
                reader = csv.reader(text_stream, delimiter='\t', quoting=csv.QUOTE_NONE)
                
                for row_num, row in enumerate(reader, 1):
                    if not row or len(row) != 10 : # altnames has 10 columns
                        if row: # Only print warning if row is not completely empty
                             print(f"Warning: Row {row_num} in {text_filename_in_zip} from {zip_filename}: Skipping malformed row (expected 10, got {len(row)}): {row}")
                        continue
                    
                    try:
                        # Type conversions for altnames
                        alt_id = int(row[0]) if row[0] else None
                        geo_id = int(row[1]) if row[1] else None
                        iso_lang = row[2]
                        alt_name = row[3]
                        # For boolean-like fields, convert '1' to 1, '0' or empty to 0 (or None if preferred for DB NULL)
                        # Assuming schema expects INTEGER, None might be better if field can be truly unknown vs false.
                        # Given original sed, they were likely treated as text or numeric if possible.
                        # Let's use `int(val) if val else None` for flexibility or `val if val else None` if they can be text.
                        # Schema states INTEGER, so let's try to cast or use None.
                        is_pref = int(row[4]) if row[4] else None 
                        is_short = int(row[5]) if row[5] else None
                        is_colloq = int(row[6]) if row[6] else None
                        is_hist = int(row[7]) if row[7] else None
                        from_d = row[8] if row[8] else None # TEXT
                        to_d = row[9] if row[9] else None   # TEXT

                        batch.append((alt_id, geo_id, iso_lang, alt_name, is_pref, is_short, is_colloq, is_hist, from_d, to_d))
                        processed_rows_in_file += 1
                        if len(batch) >= BATCH_SIZE:
                            c.executemany(sql_insert, batch)
                            conn.commit()
                            batch = []
                    except ValueError as ve:
                        print(f"Warning: Row {row_num} in {text_filename_in_zip} from {zip_filename}: Error converting value: {ve} - Row: {row}")
            
            if batch:
                c.executemany(sql_insert, batch)
                conn.commit()
            print(f"Successfully loaded {processed_rows_in_file} records from {text_filename_in_zip} (in {zip_filename}) into {target_table}.")

            # Populate countryaltnames table (this part remains SQL-based)
            print(f'Populating countryaltnames table from {target_table}...')
            with conn:
                c.execute('DELETE FROM countryaltnames;')
                # Original query: INSERT INTO countryaltnames SELECT * from altnames where geonameid in (select geonameid from countryinfo);
                # This assumes countryinfo table is already populated.
                c.execute("INSERT INTO countryaltnames SELECT * FROM altnames WHERE geonameId IN (SELECT geonameId FROM countryinfo WHERE geonameId IS NOT NULL)")
            print("Successfully populated countryaltnames table.")

    except sqlite3.Error as e_sqlite:
        conn.rollback()
        print(f"SQLite error processing file {zip_filename}: {e_sqlite}.")
    except Exception as e_file:
        # conn.rollback() # May not be needed if main try block handles it, or if commits are per batch
        print(f"General error processing file {zip_filename}: {e_file}")
    print('#'*COLS)

def load_admincodes():
    files_to_process = ['admin1CodesASCII.txt', 'admin2Codes.txt']
    BATCH_SIZE = 1000
    
    print('='*COLS)
    print(f"Processing admin codes files into admincodes table")
    print('='*COLS)

    try:
        # Delete existing records once before processing any files
        with conn:
            c.execute('DELETE FROM admincodes;')
        print("Removed existing entries from admincodes table.")

        sql = "INSERT INTO admincodes (code, name, asciiname, geonameId) VALUES (?, ?, ?, ?)"
        
        for file_basename in files_to_process:
            filepath = SOURCE.joinpath(file_basename)
            if not filepath.exists():
                print(f"Warning: File {file_basename} not found at {filepath}. Skipping.")
                continue

            print(f"Processing {file_basename}...")
            batch = []
            processed_rows_in_file = 0
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
                    
                    for row_num, row in enumerate(reader, 1):
                        if not row: continue # Skip empty rows
                        
                        if len(row) == 4:
                            try:
                                code = row[0]
                                name = row[1]
                                asciiname = row[2]
                                geonameId = int(row[3]) if row[3] else None
                                
                                batch.append((code, name, asciiname, geonameId))
                                processed_rows_in_file += 1

                                if len(batch) >= BATCH_SIZE:
                                    c.executemany(sql, batch)
                                    conn.commit()
                                    batch = []
                            except ValueError as ve:
                                print(f"Warning: Row {row_num} in {file_basename}: Error converting geonameId: {ve} - Row: {row}")
                            except IndexError: # Should not happen if len(row) == 4
                                print(f"Warning: Row {row_num} in {file_basename}: Malformed row (not enough columns): {row}")
                        elif row: # Non-empty row, but not 4 columns
                            print(f"Warning: Row {row_num} in {file_basename}: Skipping malformed row (expected 4 columns, got {len(row)}): {row}")
                
                if batch: # Insert any remaining rows for the current file
                    c.executemany(sql, batch)
                    conn.commit()
                print(f"Successfully loaded {processed_rows_in_file} records from {file_basename}.")

            except sqlite3.Error as e_sqlite: # Errors during DB operations for this file
                conn.rollback()
                print(f"SQLite error processing file {file_basename}: {e_sqlite}. Rolled back changes for this file.")
            except Exception as e_file: # Errors during file reading/processing for this file
                print(f"General error processing file {file_basename}: {e_file}")
                # Decide if a rollback is needed if some batches from this file were already committed.
                # For simplicity, if an error occurs mid-file, previous batches from THIS file are committed.
                # The main DELETE is a separate transaction.

    except sqlite3.Error as e_main: # Error with the initial DELETE
        conn.rollback()
        print(f"SQLite error during initial delete from admincodes: {e_main}")
    except Exception as e_outer: # Other unexpected errors
        print(f"An unexpected error occurred in load_admincodes: {e_outer}")
    
    print('#'*COLS)

def load_timezones():
    file = "timeZones.txt"
    filepath = SOURCE.joinpath(file)
    BATCH_SIZE = 1000

    if filepath.exists():
        print(f"Processing {file} into timezones table...")
        try:
            with conn: # Use context manager for automatic commit/rollback on initial DELETE
                c.execute('DELETE FROM timezones;')
            
            batch = []
            # Table: timezones (country, timezoneid, GMT_offset, DST_offset, RAW_offset) - 5 columns.
            sql = "INSERT INTO timezones (country, timezoneid, GMT_offset, DST_offset, RAW_offset) VALUES (?, ?, ?, ?, ?)"
            
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
                try:
                    next(reader) # Skip header row
                except StopIteration:
                    print(f"Warning: File {file} is empty or has no header.")
                    return 
                
                for row_num, row in enumerate(reader, 1):
                    if not row: continue # Skip completely empty rows
                    if len(row) == 5:
                        # All fields are TEXT as per schema and original import logic
                        batch.append((row[0], row[1], row[2], row[3], row[4]))
                        if len(batch) >= BATCH_SIZE:
                            c.executemany(sql, batch)
                            conn.commit() # Commit current batch
                            batch = []
                    elif len(row) > 0 and row[0].startswith('#'): # Skip comment lines, if any
                        continue
                    else:
                        # Handle rows with unexpected number of columns if necessary, or log them
                        print(f"Warning: Skipping malformed row {row_num} in {file} (expected 5 columns): {row}")
                
                if batch: # Insert any remaining rows
                    c.executemany(sql, batch)
                    conn.commit() # Commit final batch
            print(f"Successfully loaded {file} into timezones table.")
        except sqlite3.Error as e:
            conn.rollback() # Rollback on error
            print(f"SQLite error during loading {file}: {e}")
        except Exception as e:
            conn.rollback() # Rollback on error
            print(f"General error processing file {file}: {e}")
    else:
        print(f"File {file} not found in {SOURCE}")
    print('#'*COLS) # Original script's separator

def load_languages():
    file = "iso-languagecodes.txt"
    filepath = SOURCE.joinpath(file)
    BATCH_SIZE = 1000

    if filepath.exists():
        print(f"Processing {file} into languages table...")
        try:
            with conn: # Use context manager for automatic commit/rollback
                c.execute('DELETE FROM languages;')
            
            batch = []
            sql = "INSERT INTO languages (ISO639_3, ISO639_2, ISO639_1, language) VALUES (?, ?, ?, ?)"
            
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
                try:
                    next(reader) # Skip header row
                except StopIteration:
                    print(f"Warning: File {file} is empty or has no header.")
                    return # Or handle as appropriate
                
                for row_num, row in enumerate(reader, 1):
                    if not row: continue # Skip completely empty rows
                    if len(row) == 4 : # Expecting 4 columns: ISO639_3, ISO639_2, ISO639_1, language
                        # All fields are TEXT, so direct assignment is okay.
                        # Handle if any part of the key is empty, though usually not expected for this file.
                        iso3, iso2, iso1, lang_name = row[0], row[1], row[2], row[3]
                        batch.append((iso3, iso2, iso1, lang_name))
                        if len(batch) >= BATCH_SIZE:
                            c.executemany(sql, batch)
                            conn.commit() # Commit current batch
                            batch = []
                    elif len(row) > 0 and row[0].startswith('#'): # Skip comment lines if any (though not typical for body)
                        continue
                    else:
                        print(f"Warning: Skipping malformed row {row_num} in {file}: {row}")

                if batch: # Insert any remaining rows
                    c.executemany(sql, batch)
                    conn.commit() # Commit final batch
            print(f"Successfully loaded {file} into languages table.")
        except sqlite3.Error as e:
            conn.rollback() # Rollback on error
            print(f"SQLite error during loading {file}: {e}")
        except Exception as e:
            conn.rollback() # Rollback on error
            print(f"General error processing file {file}: {e}")
    else:
        print(f"File {file} not found in {SOURCE}")
    print('#'*COLS) # Original script's separator

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
    start_time = time.time()
    main() # This calls setupdb()
    end_time = time.time()
    print(f"Total execution time for geosqlite (setupdb): {end_time - start_time:.2f} seconds")
