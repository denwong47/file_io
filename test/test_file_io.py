import os, sys
os.chdir(os.path.dirname(sys.argv[0]))

import secrets

from file_io import file
import quicktest
unittest = quicktest

# url
_local_path = "data/test_url.bytes"
_remote_cache = f"{_local_path}.cache"
_url = f"https://github.com/denwong47/file_io/blob/main/test/{_local_path}?raw=true"

# file exist, creation and deletion
_test_folder_path = "sandbox"
_test_subfolder_path = f"{_test_folder_path}/subfolder"
_test_file_path = f"{_test_folder_path}/test_file.bytes"


class TestFileIO(unittest.TestCase):

    @classmethod
    def removeTemps(cls) -> None:
        _remote_file = file(_remote_cache, is_dir=False)
        _remote_file.delete()

        _test_file = file(_test_file_path, is_dir=False)
        _test_file.delete()

        _test_subfolder = file(_test_subfolder_path, is_dir=True)
        _test_subfolder.delete()

        _test_folder = file(_test_folder_path, is_dir=True)
        _test_folder.delete()

        # ensure everything is not found before testing
        assert not (
            _remote_file.exists() or \
            _test_file.exists() or \
            _test_folder.exists()
        )

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.removeTemps()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

        cls.removeTemps()

    def test_url(self):
        _local_file = file(_local_path)
        _remote_file = file.wget(_url, _remote_cache)

        _remote_path = _remote_file.abspath()

        # Test file.wget() success
        self.assertTrue(_remote_file)

        _local_data = _local_file.read(output=bytes)
        _remote_data = _remote_file.read(output=bytes)

        # Test file.wget() data
        self.assertEqual(_local_data, _remote_data)

        # Test file.delete()
        _remote_file.delete()
        self.assertFalse(os.path.exists(_remote_path))

    def test_file_exists(self):
        _test_file = file(_test_file_path, is_dir=False)
        _test_subfolder = file(_test_subfolder_path, is_dir=True)
        _test_folder = file(_test_folder_path, is_dir=True)

        # Create a nested folder structure        
        _test_subfolder.touch()

        # Test if BOTH directories exist
        self.assertTrue(_test_subfolder.exists())
        self.assertTrue(_test_folder.exists())

        # Remove the subfolder
        _test_subfolder.delete()
        _test_folder.delete()
        self.assertFalse(_test_subfolder.exists())
        self.assertFalse(_test_folder.exists())

        # Touch file in a non-existent folder
        _test_file.touch()
        self.assertEqual(_test_file.size(), 0)
        self.assertTrue(_test_file.exists())
        self.assertTrue(_test_folder.exists())

        # Delete file
        _test_file.delete()

        # Save file in an existing folder
        _data = secrets.token_bytes(4096)
        _test_file.write(_data, overwrite=True)
        self.assertEqual(_test_file.size(), len(_data))
        self.assertTrue(_test_file.exists())
        self.assertTrue(_test_folder.exists())

        # Read the file
        self.assertEqual(
            _data,
            _test_file.read(output=bytes)
        )

        # Delete file
        _test_file.delete()
        self.assertFalse(_test_file.exists())

        _test_folder.delete()
        self.assertFalse(_test_folder.exists())
        

if (__name__=="__main__"):
    unittest.main()