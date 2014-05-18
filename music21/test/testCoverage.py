# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         test.testCoverage.py
# Purpose:      Generate an HTML report on the current state of our code test coverage
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012-14 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------
from __future__ import unicode_literals


# sudo easy_install coverage

try:
    import coverage
except ImportError:
    coverage = None
    
import music21
from music21.test import testSingleCoreAll as testModule
#from music21 import bar
#import webbrowser

def runCoverage(show=True):
    if coverage is None:
        raise music21.Music21Exception("Cannot run test.testCoverage unless the coverage Python library is installed; sudo easy_install coverage")
    
    cov = coverage.coverage()
    cov.start()
    testModule.main()
    #music21.mainTest(bar.Test)
    cov.stop()
    cov.html_report(directory='/Users/cuthbert/web/music21/coverage/')

if __name__ == "__main__":
    runCoverage()