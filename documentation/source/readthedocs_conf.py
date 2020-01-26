# Configuration file for readthedocs
# builds everything before sphinx

# import all conf settings
from conf import *

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from docbuild.make import DocBuilder

if __name__ == '__main__':
    db = DocBuilder()
    db.runBuild(runSphinx=False)

