# tests/test_setup_scripts.py
import unittest
from unittest.mock import patch, mock_open, MagicMock
import sqlite3
import os
from pathlib import Path
import shutil # For cleaning up test artifacts

# Attempt to import the modules to be tested
try:
    from pynations import geodownloader
    from pynations import geosqlite
except ImportError as e:
    # This allows tests to be skipped if pynations structure is not fully set up in test environment
    # Or, adjust sys.path if needed, but for now, this handles potential import issues in CI.
    print(f"Skipping test_setup_scripts due to import error: {e}")
    geodownloader = None
    geosqlite = None

# Define a temporary data directory for tests
TEST_DATA_DIR = Path("test_geonamesdata_temp")
TEST_DB_FILE = Path("test_pynations_temp.sqlite")

@unittest.skipIf(geosqlite is None, "pynations.geosqlite not available")
class TestGeoSQLiteLoading(unittest.TestCase):
    def setUp(self):
        # Create a temporary data source directory
        TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Point geosqlite.SOURCE and geosqlite.DBFILE to test locations
        self.original_source = geosqlite.SOURCE
        self.original_dbfile = geosqlite.DBFILE
        geosqlite.SOURCE = TEST_DATA_DIR
        geosqlite.DBFILE = TEST_DB_FILE
        # Ensure a fresh db for each test method if geosqlite.conn is module level
        if TEST_DB_FILE.exists():
            TEST_DB_FILE.unlink()
        
        # Re-establish connection and cursor for geosqlite module
        # This is because conn and c are module-level globals in geosqlite.py
        if geosqlite.conn: # Close existing connection if any
            geosqlite.conn.close()
        geosqlite.conn = sqlite3.connect(str(TEST_DB_FILE)) 
        geosqlite.c = geosqlite.conn.cursor()
        
        # Since table creation in geosqlite.py is conditional on dbexists (which is also module level and not re-evaluated)
        # and happens on import, we need to manually ensure tables for the test DB.
        # For this specific test, we only need the 'languages' table.
        # A more robust setup would have a dedicated function in geosqlite to init tables.
        with geosqlite.conn:
            geosqlite.c.execute('''CREATE TABLE IF NOT EXISTS languages (
                                       ISO639_3 TEXT, ISO639_2 TEXT, 
                                       ISO639_1 TEXT, language TEXT)''')
            geosqlite.c.execute("CREATE INDEX IF NOT EXISTS languages_idx1 on languages(ISO639_2);")


    def tearDown(self):
        # Clean up
        if geosqlite.conn:
            geosqlite.conn.close()
            # Nullify to avoid issues if tests are run multiple times in same session with pytest collection
            geosqlite.conn = None
            geosqlite.c = None

        if TEST_DB_FILE.exists():
            TEST_DB_FILE.unlink()
        if TEST_DATA_DIR.exists():
            shutil.rmtree(TEST_DATA_DIR)
        # Restore original paths
        geosqlite.SOURCE = self.original_source
        geosqlite.DBFILE = self.original_dbfile
        # Reconnect original DB if it was meant to be persistent (outside test scope)
        # For now, assume original paths are restored for subsequent non-test operations if any.


    def test_load_languages_refactored(self):
        # Dummy file content for iso-languagecodes.txt
        dummy_lang_file_content = "ISO639-3\tISO639-2\tISO639-1\tLanguage Name\n" \
                                  "aar\taa\taa\tAfar\n" \
                                  "abk\tab\tab\tAbkhazian\n"
        dummy_file_path = TEST_DATA_DIR / "iso-languagecodes.txt"
        with open(dummy_file_path, 'w', encoding='utf-8') as f:
            f.write(dummy_lang_file_content)
        
        # Patch findFiles to return our dummy file.
        # `files` is a global in geosqlite, used by load_countryinfo but not directly by load_languages.
        # load_languages directly uses SOURCE.joinpath("iso-languagecodes.txt").
        # So, findFiles patch is not strictly needed for load_languages if it constructs path directly.
        # However, if other parts of geosqlite rely on `files` being populated by findFiles,
        # and if load_languages was part of a setupdb() call that uses it, it might be relevant.
        # For an isolated test of load_languages, ensuring the file exists at geosqlite.SOURCE is key.
        
        # Call the function to test
        geosqlite.load_languages()

        # Assert data
        # Re-create cursor on the connection for this check, as it might have been closed or become invalid
        cursor = geosqlite.conn.cursor() 
        cursor.execute("SELECT ISO639_1, language FROM languages WHERE ISO639_1 = 'aa'")
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result, ('aa', 'Afar'))
        
        cursor.execute("SELECT COUNT(*) FROM languages")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)

@unittest.skipIf(geodownloader is None, "pynations.geodownloader not available")
class TestGeonamesDownloader(unittest.TestCase):
    def setUp(self):
        # Create a temporary data destination directory
        TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Patch geodownloader.DESTINATION
        self.original_destination = geodownloader.DESTINATION
        geodownloader.DESTINATION = TEST_DATA_DIR
        
        # Instantiate downloader after patching DESTINATION
        self.downloader = geodownloader.GeonamesDownloader()
       
    def tearDown(self):
        if TEST_DATA_DIR.exists():
            shutil.rmtree(TEST_DATA_DIR)
        # Restore original DESTINATION
        geodownloader.DESTINATION = self.original_destination

    @patch('requests.get')
    def test_download_supporting_info_mocked(self, mock_requests_get):
        # Simulate successful downloads
        mock_response = MagicMock()
        mock_response.status_code = 200
        # For iter_content used by _download_file_worker (binary files)
        mock_response.iter_content.return_value = [b"some ", b"file ", b"content"]
        # For .content.decode used by older single-file downloads (text files)
        mock_response.content = b"some text content"
        mock_requests_get.return_value = mock_response

        # Suppress print statements from the downloader during test
        with patch('builtins.print'):
            # download_supporting_info now uses _download_file_worker
            self.downloader.download_supporting_info()

        # Assert requests.get was called for each URL in download_supporting_info
        # There are 4 URLs in download_supporting_info
        self.assertEqual(mock_requests_get.call_count, 4) 
        
        # Check if files were "created" (mocked content)
        self.assertTrue((TEST_DATA_DIR / "timeZones.txt").exists())
        self.assertTrue((TEST_DATA_DIR / "iso-languagecodes.txt").exists())
        self.assertTrue((TEST_DATA_DIR / "admin1CodesASCII.txt").exists())
        self.assertTrue((TEST_DATA_DIR / "admin2Codes.txt").exists())


if __name__ == '__main__':
    unittest.main()
