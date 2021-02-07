# Configuration file for readthedocs
# builds everything before sphinx

import os
import sys

sys.path.insert(0, os.path.abspath('..'))
# import all conf settings
from conf import *  # noqa  # pylint: disable=import-error,wildcard-import

from docbuild.make import DocBuilder  # noqa

if __name__ == '__main__':
    db = DocBuilder()
    db.runBuild(runSphinx=False)

