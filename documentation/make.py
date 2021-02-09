#!/usr/bin/env python3

import sys
from docbuild.make import DocBuilder

if __name__ == '__main__':
    if len(sys.argv) > 1:
        runMode = sys.argv[1]  # to rebuild everything run "make.py clean"
    else:
        runMode = 'html'
    db = DocBuilder(runMode)
    db.run()
