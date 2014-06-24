# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testDocumentation.py
# Purpose:      tests from or derived from the Documentation
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------
'''
Module to test all the code excerpts in the .rst files in the music21 documentation.
'''
from __future__ import print_function

import time
import os.path
import doctest

import music21
_MOD = "test.testDocumentation.py"  

skipModules = [
               'documenting.rst', # contains info that screws up testing
               ]

def main(runOne=False):
    music21init = music21.__file__
    music21basedir = os.path.dirname(music21init)
    builddocRstDir = os.path.join(music21basedir,
                                  'documentation',
                                  'source')
    
    totalTests = 0
    totalFailures = 0
    
    timeStart = time.time()

    if not os.path.exists(builddocRstDir):
        raise Exception("Cannot run tests on documentation because the rst files in documentation/source do not exist")
    
    for root, unused_dirnames, filenames in os.walk(builddocRstDir):
        for module in filenames:
            fullModulePath = os.path.join(root, module)
            if not module.endswith('.rst'):
                continue
            if module.startswith('module'):
                continue
            if module in skipModules:
                continue
            if runOne is not False:
                if not module.endswith(runOne):
                    continue
            
            moduleNoExtension = module[:-4]
            if moduleNoExtension + '.ipynb' in filenames:
                continue
            
            #print fullModulePath
            print(module + ":", end="")
            try:
                (failcount, testcount) = doctest.testfile(fullModulePath, module_relative = False, optionflags = doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
                if failcount > 0:
                    print("%s had %d failures in %d tests" % (module, failcount, testcount))
                elif testcount == 0:
                    print("no tests")
                else:
                    print("all %d tests ran successfully" % (testcount))
                totalTests += testcount
                totalFailures += failcount
            except Exception as e:
                print("failed miserably! %s" % str(e))
                import traceback
                tb = traceback.format_exc()
                print("Here's the traceback for the exeception: \n%s" % (tb))


    elapsedTime = time.time() - timeStart
    print("Ran %d tests (%d failed) in %.4f seconds" % (totalTests, totalFailures, elapsedTime))


if __name__ == '__main__':
    main()
    #main('usersGuide_05_listsOfLists.rst')