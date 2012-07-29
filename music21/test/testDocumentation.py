# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testDocumentation.py
# Purpose:      tests from or derived from the Documentation
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2010-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Module to test all the code excerpts in the rst files in the music21 documentation.
'''


import time
import os, os.path
import doctest, unittest

import music21
_MOD = "test.testDocumentation.py"  

skipModules = [
               'documenting.rst', # contains info the screws up testing
               ]

def main():
    music21init = music21.__file__
    music21dir = os.path.dirname(music21init)
    music21basedir = os.path.dirname(music21dir)
    builddocRstDir = music21basedir + os.sep + 'builddoc' + os.sep + 'rst'
    
    totalTests = 0
    totalFailures = 0
    
    timeStart = time.time()

    if not os.path.exists(builddocRstDir):
        raise Exception("Cannot run tests on documentation because the rst files in builddoc do not exist")
    
    for module in os.listdir(builddocRstDir):
        if not module.endswith('.rst'):
            continue
        if module.startswith('module'):
            continue
        if module in skipModules:
            continue
        fullModulePath = builddocRstDir + os.sep + module
        print module + ":",
        (failcount, testcount) = doctest.testfile(fullModulePath, optionflags = doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
        if failcount > 0:
            print "%s had %d failures in %d tests" % (module, failcount, testcount)
        elif testcount == 0:
            print "no tests"
        else:
            print "all %d tests ran successfully" % (testcount)
        totalTests += testcount
        totalFailures += failcount

    elapsedTime = time.time() - timeStart
    print "Ran %d tests (%d failed) in %.4f seconds" % (totalTests, totalFailures, elapsedTime)


if __name__ == '__main__':
    main()