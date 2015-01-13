# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testDocumentation.py
# Purpose:      tests from or derived from the Documentation
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Module to test all the code excerpts in the .rst files in the music21 documentation.
'''
from __future__ import print_function

import time
import os.path
import doctest
from collections import namedtuple

ModTuple = namedtuple('ModTuple', 'module fullModulePath moduleNoExtension isIPYNB')

_MOD = "test.testDocumentation.py"  

skipModules = [
               'documenting.rst', # contains info that screws up testing
               ]

def getDocumentationFiles(runOne=False):
    '''
    returns a list of namedtuples for each module that should be run
    
    >>> test.testDocumentation.getDocumentationFiles()
    [ModTuple(module='index.rst', fullModulePath='...music21/documentation/source/index.rst', 
    moduleNoExtension='index', isIPYNB=False),
    ...]
    '''
    from music21 import common
    music21basedir = common.getSourceFilePath()
    builddocRstDir = os.path.join(music21basedir,
                                  'documentation',
                                  'source')
    if not os.path.exists(builddocRstDir):
        raise Exception("Cannot run tests on documentation because the rst files in documentation/source do not exist")
    
    allModules = []
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
                isIPYNB = True
            else:
                isIPYNB = False
            modTuple = ModTuple(module, fullModulePath, moduleNoExtension, isIPYNB)
            allModules.append(modTuple)
    return allModules

def main(runOne=False):
    totalTests = 0
    totalFailures = 0
    
    timeStart = time.time()
    for mt in getDocumentationFiles(runOne):        
        print(mt.module + ":", end="")
        try:
            (failcount, testcount) = doctest.testfile(mt.fullModulePath, module_relative = False, optionflags = doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
            if failcount > 0:
                print("%s had %d failures in %d tests" % (mt.module, failcount, testcount))
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
    #import music21
    #music21.mainTest()
    main()
    #main('usersGuide_11_corpusSearching.rst')
    #main('overviewPostTonal.rst')