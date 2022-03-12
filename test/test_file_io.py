import os, sys
os.chdir(os.path.dirname(sys.argv[0]))

import secrets

from file_io import file
import quicktest
unittest = quicktest

class TestFileIO(unittest.TestCase):
    pass

if (__name__=="__main__"):
    unittest.main()