#!/usr/bin/env python3

from docbuild.make import DocBuilder # @UnresolvedImport
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        runMode = sys.argv[1]   # to rebuild everything run "make.py clean"
    else:
        runMode = 'html'
    db = DocBuilder(runMode)
    db.run()
